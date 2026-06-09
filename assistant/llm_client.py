#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LLM client using Ollama via HTTP requests.

Adapted from the reference alarm project:
  voice_control/qwen_assistant.py -> ask_qwen()

Uses requests.Session for lightweight HTTP calls instead of
the ollama Python SDK (saves dependencies on Pi).
"""

import json

import requests

import config
from assistant.speech_format import make_reply_informal


class LLMClient:
    """Wraps the Ollama REST API for local LLM chat completions."""

    def __init__(self, model=config.OLLAMA_MODEL):
        self._model = model
        self._session = requests.Session()
        self._messages = []
        self._current_language = None
        print(f"[LLM] Ready: {model} via Ollama")

    def chat(self, user_message, language):
        """
        Send a message to the LLM and get a response.

        Adapted from reference project's ask_qwen().

        Args:
            user_message: The transcribed user speech.
            language: Detected language code ("en" or "de").

        Returns:
            The assistant's response text.
        """
        # Reset conversation if language changed
        if language != self._current_language:
            self._messages = []
            self._current_language = language

        # Build system message
        system_prompt = config.SYSTEM_PROMPTS.get(
            language, config.SYSTEM_PROMPTS["en"]
        )
        system_msg = {"role": "system", "content": system_prompt}

        # Add user message
        self._messages.append({"role": "user", "content": user_message})

        # Trim history (keep system + last N messages)
        while len(self._messages) > config.MAX_CONVERSATION_HISTORY:
            self._messages.pop(0)

        # Build payload (matching reference project pattern)
        payload = {
            "model": self._model,
            "messages": [system_msg] + self._messages,
            "stream": False,
            "think": False,
            "keep_alive": "2m",
            "options": config.OLLAMA_OPTIONS,
        }

        try:
            response = self._session.post(
                config.OLLAMA_URL,
                json=payload,
                timeout=config.OLLAMA_TIMEOUT,
            )
            response.raise_for_status()

            data = response.json()
            answer = data.get("message", {}).get("content", "").strip()

            # Strip Qwen thinking tags (from reference)
            if "</think>" in answer:
                answer = answer.split("</think>", 1)[-1].strip()

            if not answer:
                print("[LLM] Empty response from Ollama")
                print(json.dumps(data, indent=2, ensure_ascii=False))
                if language == "de":
                    answer = "Ich habe gerade keine passende Antwort erzeugt."
                else:
                    answer = "I couldn't generate a response right now."

            # Apply informal style for German (from reference)
            if language == "de":
                answer = make_reply_informal(answer)

            # Save to history
            self._messages.append({"role": "assistant", "content": answer})

            return answer

        except requests.exceptions.ConnectionError:
            print("[!!] Ollama is not reachable")
            if language == "de":
                return "Entschuldigung, Ollama ist gerade nicht erreichbar."
            return "Sorry, Ollama is not reachable right now."

        except requests.exceptions.Timeout:
            print("[!!] Ollama timed out")
            if language == "de":
                return "Entschuldigung, die Antwort hat zu lange gedauert."
            return "Sorry, the response took too long."

        except Exception as exc:
            print(f"[!!] Ollama error: {exc}")
            if language == "de":
                return "Entschuldigung, es gab einen Fehler."
            return "Sorry, there was an error."

    def reset_conversation(self):
        """Clear conversation history."""
        self._messages = []
        self._current_language = None
        print("[LLM] Conversation reset")

    def close(self):
        """Close the HTTP session."""
        self._session.close()
