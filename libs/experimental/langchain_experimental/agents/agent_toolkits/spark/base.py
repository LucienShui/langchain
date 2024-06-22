"""Agent for working with pandas objects."""
from typing import Any, Dict, List, Optional

from langchain.agents.agent import AgentExecutor
from langchain.agents.mrkl.base import ZeroShotAgent
from langchain.chains.llm import LLMChain
from langchain_core.callbacks.base import BaseCallbackManager
from langchain_core.language_models import BaseLLM

from langchain_experimental.agents.agent_toolkits.spark.prompt import PREFIX, SUFFIX
from langchain_experimental.tools.python.tool import PythonAstREPLTool


def _validate_spark_df(df: Any) -> bool:
    try:
        from pyspark.sql import DataFrame as SparkLocalDataFrame

        return isinstance(df, SparkLocalDataFrame)
    except ImportError:
        return False


def _validate_spark_connect_df(df: Any) -> bool:
    try:
        from pyspark.sql.connect.dataframe import DataFrame as SparkConnectDataFrame

        return isinstance(df, SparkConnectDataFrame)
    except ImportError:
        return False


def create_spark_dataframe_agent(
    llm: BaseLLM,
    df: Any,
    callback_manager: Optional[BaseCallbackManager] = None,
    prefix: str = PREFIX,
    suffix: str = SUFFIX,
    input_variables: Optional[List[str]] = None,
    verbose: bool = False,
    return_intermediate_steps: bool = False,
    max_iterations: Optional[int] = 15,
    max_execution_time: Optional[float] = None,
    early_stopping_method: str = "force",
    agent_executor_kwargs: Optional[Dict[str, Any]] = None,
    allow_dangerous_code: bool = False,
    **kwargs: Any,
) -> AgentExecutor:
    """Construct a Spark agent from an LLM and dataframe.

    Security Notice:
        This agent relies on access to a python repl tool which can execute
        arbitrary code. This can be dangerous and requires a specially sandboxed
        environment to be safely used. Failure to run this code in a properly
        sandboxed environment can lead to arbitrary code execution vulnerabilities,
        which can lead to data breaches, data loss, or other security incidents.

        Do not use this code with untrusted inputs, with elevated permissions,
        or without consulting your security team about proper sandboxing!

        You must opt in to use this functionality by setting allow_dangerous_code=True.

    Args:
        allow_dangerous_code: bool, default False
            This agent relies on access to a python repl tool which can execute
            arbitrary code. This can be dangerous and requires a specially sandboxed
            environment to be safely used.
            Failure to properly sandbox this class can lead to arbitrary code execution
            vulnerabilities, which can lead to data breaches, data loss, or
            other security incidents.
            You must opt in to use this functionality by setting
            allow_dangerous_code=True.
    """
    if not allow_dangerous_code:
        raise ValueError(
            "This agent relies on access to a python repl tool which can execute "
            "arbitrary code. This can be dangerous and requires a specially sandboxed "
            "environment to be safely used. Please read the security notice in the "
            "doc-string of this function. You must opt-in to use this functionality "
            "by setting allow_dangerous_code=True."
            "For general security guidelines, please see: "
            "https://python.langchain.com/v0.2/docs/security/"
        )

    if not _validate_spark_df(df) and not _validate_spark_connect_df(df):
        raise ImportError("Spark is not installed. run `pip install pyspark`.")

    if input_variables is None:
        input_variables = ["df", "input", "agent_scratchpad"]
    tools = [PythonAstREPLTool(locals={"df": df})]
    prompt = ZeroShotAgent.create_prompt(
        tools, prefix=prefix, suffix=suffix, input_variables=input_variables
    )
    partial_prompt = prompt.partial(df=str(df.first()))
    llm_chain = LLMChain(
        llm=llm,
        prompt=partial_prompt,
        callback_manager=callback_manager,
    )
    tool_names = [tool.name for tool in tools]
    agent = ZeroShotAgent(  # type: ignore[call-arg]
        llm_chain=llm_chain,
        allowed_tools=tool_names,
        callback_manager=callback_manager,
        **kwargs,
    )
    return AgentExecutor.from_agent_and_tools(
        agent=agent,
        tools=tools,
        callback_manager=callback_manager,
        verbose=verbose,
        return_intermediate_steps=return_intermediate_steps,
        max_iterations=max_iterations,
        max_execution_time=max_execution_time,
        early_stopping_method=early_stopping_method,
        **(agent_executor_kwargs or {}),
    )
