"""Standard LangChain interface tests"""

import os
from typing import Type

from langchain_core.language_models import BaseChatModel
from langchain_standard_tests.integration_tests import ChatModelIntegrationTests  # type: ignore[import-not-found]

from langchain_openai import AzureChatOpenAI

OPENAI_API_VERSION = os.environ.get("AZURE_OPENAI_API_VERSION", "")
OPENAI_API_BASE = os.environ.get("AZURE_OPENAI_API_BASE", "")
OPENAI_API_KEY = os.environ.get("AZURE_OPENAI_API_KEY", "")
DEPLOYMENT_NAME = os.environ.get(
    "AZURE_OPENAI_DEPLOYMENT_NAME",
    os.environ.get("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME", ""),
)


class TestOpenAIStandard(ChatModelIntegrationTests):
    @property
    def chat_model_class(self) -> Type[BaseChatModel]:
        return AzureChatOpenAI

    @property
    def chat_model_params(self) -> dict:
        return {
            "deployment_name": DEPLOYMENT_NAME,
            "openai_api_version": OPENAI_API_VERSION,
            "azure_endpoint": OPENAI_API_BASE,
            "api_key": OPENAI_API_KEY,
        }
