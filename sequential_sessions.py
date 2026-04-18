"""
User Story → Technical Spec → Flask Code
Using github-copilot-sdk (no LangChain)

Install:
    pip install github-copilot-sdk

Auth: the SDK reads credentials from the Copilot CLI login.
Run `copilot auth login` once before executing this script.

This script demonstrates a sequential session workflow where the output of one session (technical specifications) is used as the input for another session (code generation). It uses streaming responses to collect the full output from each session before proceeding to the next step.
The initial version of this script was created using Claude Sonnet 4.6 from the transformation chain example at https://langchain-tutorials.com/lessons/langchain-essentials/lesson-7
"""

import asyncio
from copilot import CopilotClient
from copilot.session import PermissionHandler

MODEL_NAME = "claude-haiku-4.5"  # You can choose other models like "gpt-4.1" or "gpt-3.5-turbo"

async def send_and_collect(session, prompt: str) -> str:
    """Send a prompt and collect the full response text."""
    chunks: list[str] = []
    done = asyncio.Event()

    def on_event(event):
        match event.type.value:
            case "assistant.message_delta":
                chunks.append(event.data.delta_content or "")
            case "session.idle":
                done.set()

    session.on(on_event)
    await session.send(prompt)
    await done.wait()
    return "".join(chunks)


async def main():
    user_story = (
        "As a user, I want to create and manage todo items with due dates"
    )

    async with CopilotClient() as client:

        # ── Step 1: User story → Technical spec ──────────────────────────
        async with await client.create_session(
            on_permission_request=PermissionHandler.approve_all,
            model=MODEL_NAME,
            streaming=True,
        ) as session:
            spec_prompt = f"""
Convert this user story into a technical specification with clear requirements
and acceptance criteria:

{user_story}

Include: endpoints, data models, and validation rules.
"""
            specifications = await send_and_collect(session, spec_prompt)

        # ── Step 2: Technical spec → Flask implementation ─────────────────
        async with await client.create_session(
            on_permission_request=PermissionHandler.approve_all,
            model=MODEL_NAME,
            streaming=True,
        ) as session:
            code_prompt = f"""
Write a Python Flask implementation based on this technical specification:

{specifications}

Include proper error handling and documentation.
"""
            generated_code = await send_and_collect(session, code_prompt)

    # ── Display results ───────────────────────────────────────────────────
    print("Original User Story:")
    print(user_story)
    print("\n" + "=" * 50 + "\n")
    print("Technical Specifications:")
    print(specifications)
    print("\n" + "=" * 50 + "\n")
    print("Generated Code:")
    print(generated_code)

    with open("generated_code.py", "w") as f:
        f.write(generated_code)
        print("\nGenerated code written to generated_code.py")


if __name__ == "__main__":
    asyncio.run(main())