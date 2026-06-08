"""
Lightweight Ollama client using HTTP requests.

Posts to the local Ollama REST API at `config.OLLAMA_URL` and
maintains a small conversation history to preserve short context.
"""

import requests
from typing import List

import config


class LLMClient:
    def __init__(self, model: str = config.OLLAMA_MODEL):
        self._model = model
        self._history: List[dict] = []
        self._language = None
        self._session = requests.Session()
        print(f"[LLM] Ready: {model} via HTTP {config.OLLAMA_URL}")

    def chat(self, user_message: str, language: str) -> str:
        # Reset when language changes
        if language != self._language:
            self._history = []
            self._language = language

        system_prompt = config.SYSTEM_PROMPTS.get(language, config.SYSTEM_PROMPTS["en"])

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(self._history)
        messages.append({"role": "user", "content": user_message})

        payload = {
            "model": self._model,
            "messages": messages,
            "options": config.OLLAMA_OPTIONS,
        }

        try:
            resp = self._session.post(config.OLLAMA_URL, json=payload, timeout=config.OLLAMA_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()

            # Try to extract assistant message from common shapes
            assistant_text = ""
            if "message" in data and isinstance(data["message"], dict):
                assistant_text = data["message"].get("content", "")
            elif "choices" in data and data["choices"]:
                # format: choices[0].message.content
                c = data["choices"][0]
                assistant_text = c.get("message", {}).get("content", c.get("text", ""))
            else:
                assistant_text = data.get("response", "")

            assistant_text = assistant_text or ""

            # Post-process German replies to be informal
            if language == "de":
                from assistant.speech_format import make_reply_informal

                assistant_text = make_reply_informal(assistant_text)

            # Update history and trim
            self._history.append({"role": "user", "content": user_message})
            self._history.append({"role": "assistant", "content": assistant_text})

            max_entries = config.MAX_CONVERSATION_HISTORY * 2
            if len(self._history) > max_entries:
                self._history = self._history[-max_entries:]

            return assistant_text

        except requests.RequestException as e:
            print(f"  [!!] Ollama request error: {e}")
            if language == "de":
                return "Ich kann Ollama nicht erreichen. Ist der Server gestartet?"
            return "I can't reach Ollama. Is the server running?"

    def reset_conversation(self) -> None:
        self._history = []
        self._language = None
        print("  [OK] Conversation reset")
