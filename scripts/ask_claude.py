import os
import argparse
import sys
import tempfile
from pathlib import Path
from anthropic import Anthropic
from pdf2image import convert_from_path


def create_claude_client():
    """Create and return an Anthropic client using API key from environment."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ANTHROPIC_API_KEY environment variable is not set.")
        sys.exit(0)
    return Anthropic(api_key=api_key)


def get_coding_system_prompt():
    """Return a system prompt optimized for coding tasks."""
    return """You are Claude, an AI assistant with extensive programming expertise. When writing code:
- Prioritize clarity, efficiency, and best practices
- Include comprehensive docstrings and comments
- Handle edge cases and errors appropriately
- Follow language-specific style guides (PEP 8 for Python, etc.)
- Provide working examples when helpful
- Break down complex problems into smaller steps
- Explain key design decisions and trade-offs
Always test and verify your code mentally before providing it."""


def get_general_system_prompt():
    """Return a system prompt optimized for logical, well-reasoned responses."""
    return """You are Claude, an AI assistant focused on providing clear, logical, and well-reasoned responses. In your analysis:
- Think through problems step by step
- Consider multiple perspectives and potential counterarguments
- Support claims with clear reasoning and evidence when possible
- Acknowledge uncertainty when appropriate
- Organize responses in a clear, structured manner
- Focus on accuracy and precision in explanations
- Maintain objectivity while providing nuanced analysis"""


def process_image(image_path, filetype=None):
    """Process image or PDF file and return appropriate message content."""
    image_path = Path(image_path)
    if not image_path.is_file():
        print(f"File not found: {image_path}")
        return None

    type_suffix = image_path.suffix.lower()
    if filetype:
        type_suffix = filetype if filetype.startswith(".") else f".{filetype}"

    if type_suffix == ".pdf":
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
            temp_file_path = Path(temp_file.name)
            images = convert_from_path(image_path, single_file=True)
            if not images:
                print("Failed to convert PDF to JPEG.")
                return None
            images[0].save(temp_file_path, "JPEG")
            image_path = Path(temp_file_path)
            temp_file.close()
    elif type_suffix not in [".png", ".jpg", ".jpeg"]:
        print(f"Unsupported file format: {type_suffix}")
        return None

    media_type = "image/png" if type_suffix == ".png" else "image/jpeg"
    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": media_type,
            "data": image_path,
        },
    }


def main():
    """Command line interface for interacting with Claude."""
    parser = argparse.ArgumentParser(
        description="Enhanced Claude API Command Line Tool"
    )
    parser.add_argument(
        "-c",
        "--code",
        action="store_true",
        help="Enable programming mode with coding-optimized system prompt",
    )
    parser.add_argument(
        "-g",
        "--message",
        action="append",
        nargs=2,
        metavar=("role", "content"),
        help="Add a message with specified role and content",
    )
    parser.add_argument("-i", "--image", type=str, help="Path to the image or PDF file")
    parser.add_argument(
        "-m",
        "--model",
        default="claude-3-5-sonnet-20240620",
        help="Specify the Claude model to use",
    )
    parser.add_argument(
        "-s", "--system", type=str, help="Override default system message"
    )
    parser.add_argument(
        "-t", "--temperature", type=float, help="Temperature for the model"
    )
    parser.add_argument("-k", "--top_k", type=int, help="Top-k sampling")
    parser.add_argument("-p", "--top_p", type=float, help="Top-p sampling")
    parser.add_argument(
        "-x",
        "--max_tokens",
        type=int,
        default=1024,
        help="Maximum tokens in response (default: 1024)",
    )
    parser.add_argument(
        "-f",
        "--filetype",
        type=str,
        help="Overwrite automatic detection of filetype (pdf, png, jpeg, jpg)",
    )
    parser.add_argument(
        "prompt",
        nargs="*",
        help="The prompt/question for Claude (optional if using --message)",
    )

    args = parser.parse_args()

    client = create_claude_client()
    messages = []

    # Process messages from -g/--message arguments
    if args.message:
        for role, content in args.message:
            messages.append({"role": role, "content": content})

    # Process prompt argument if provided
    if args.prompt:
        prompt_text = " ".join(args.prompt)
        if messages:
            if isinstance(messages[-1]["content"], list):
                messages[-1]["content"].append({"type": "text", "text": prompt_text})
            else:
                messages[-1]["content"] = [{"type": "text", "text": prompt_text}]
        else:
            messages.append({"role": "user", "content": prompt_text})

    # Process image if provided
    if args.image:
        image_message = process_image(args.image, args.filetype)
        if image_message:
            if messages:
                last_message = messages[-1]
                if isinstance(last_message["content"], list):
                    last_message["content"].append(image_message)
                else:
                    last_message["content"] = [
                        {"type": "text", "text": last_message["content"]},
                        image_message,
                    ]
            else:
                messages.append(
                    {
                        "role": "user",
                        "content": [{"type": "text", "text": ""}, image_message],
                    }
                )

    # Prepare API call arguments
    create_kwargs = {
        "max_tokens": args.max_tokens,
        "messages": messages,
        "model": args.model,
    }

    # Set system message based on mode or override
    if args.system is not None:
        create_kwargs["system"] = args.system
    elif args.code:
        create_kwargs["system"] = get_coding_system_prompt()
    else:
        create_kwargs["system"] = get_general_system_prompt()

    # Add optional parameters if provided
    if args.temperature is not None:
        create_kwargs["temperature"] = args.temperature
    if args.top_k is not None:
        create_kwargs["top_k"] = args.top_k
    if args.top_p is not None:
        create_kwargs["top_p"] = args.top_p

    try:
        # Make API call and print response
        response = client.messages.create(**create_kwargs)

        for content in response.content:
            if isinstance(content, dict) and content.get("type") == "text":
                print(content["text"])
            elif hasattr(content, "text"):
                print(content.text)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
