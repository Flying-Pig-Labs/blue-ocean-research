"""Ideation flow abstractions and simple flow implementations."""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
import json
import os
from typing import Any, Dict, List, Optional

import anthropic

from github_integration import GitHubIntegration


class IdeationFlow(ABC):
    """Interface for ideation flows that produce GitHub repos with ideas."""

    @abstractmethod
    def run(
        self,
        input_file: Optional[str] = None,
        verbose: bool = False,
        use_cache: bool = False,
        skip_github: bool = False,
        interactive: bool = False,
    ) -> None:
        """Execute the flow."""


class SimpleIdeationFlow(IdeationFlow):
    """Simple flow that makes a single Opus 4.1 call and publishes to GitHub."""

    def __init__(self, flow_type: str) -> None:
        self.flow_type = flow_type

    def _call_llm(self, research: str) -> List[Dict[str, str]]:
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        prompt = (
            f"You are an expert in {self.flow_type} opportunities. "
            "Given the research below, generate exactly 10 distinct ideas as a JSON "
            "array under the key 'ideas', where each entry has 'title' and 'description'.\n\n"
            f"Research:\n{research}"
        )
        resp = client.messages.create(
            model="opus-4.1",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        text = resp.content[0].text if resp.content else "[]"
        try:
            data = json.loads(text)
            if isinstance(data, dict) and "ideas" in data:
                return data["ideas"]
            if isinstance(data, list):
                return data
        except Exception:
            pass
        return []

    def run(
        self,
        input_file: Optional[str] = None,
        verbose: bool = False,
        use_cache: bool = False,
        skip_github: bool = False,
        interactive: bool = False,
    ) -> None:
        research = ""
        if input_file and os.path.exists(input_file):
            with open(input_file, "r") as f:
                research = f.read()
        try:
            ideas = self._call_llm(research)
        except Exception as exc:  # pragma: no cover - network failures
            print(f"LLM call failed: {exc}")
            ideas = [
                {"title": f"Placeholder idea {i+1}", "description": "Auto-generated"}
                for i in range(10)
            ]

        if skip_github:
            return

        gh = GitHubIntegration()
        gh.create_github_project(
            repo_name=f"{self.flow_type}-ideas-{datetime.now():%Y%m%d-%H%M%S}",
            research_analysis={},
            jtbd_data={},
            zones_data={},
            ideas_data={"product_ideas": ideas},
            create_issues=True,
        )


class MedicalDeviceFlow(SimpleIdeationFlow):
    def __init__(self) -> None:
        super().__init__("medical-device")


class PrivateEquityFlow(SimpleIdeationFlow):
    def __init__(self) -> None:
        super().__init__("private-equity")


class CityRevitalizationFlow(SimpleIdeationFlow):
    def __init__(self) -> None:
        super().__init__("city-revitalization")


class DataCenterFlow(SimpleIdeationFlow):
    def __init__(self) -> None:
        super().__init__("data-center")
