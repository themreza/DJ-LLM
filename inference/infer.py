"""
Inference script for Qwen3-Omni using Gradio Client.
"""

import argparse
import sys
import os
from gradio_client import Client, handle_file


def main():
    parser = argparse.ArgumentParser(
        description="Infer Qwen3-Omni via the Gradio Client",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    # Required arguments
    parser.add_argument(
        "--client",
        required=True,
        help="Client address (e.g., https://example.com/)"
    )
    parser.add_argument(
        "--text",
        required=True,
        help="Text prompt for the model"
    )
    parser.add_argument(
        "--audio",
        required=True,
        help="Path or URL to audio file"
    )

    # Optional media inputs
    parser.add_argument(
        "--image",
        help="Path or URL to image file"
    )
    parser.add_argument(
        "--video",
        help="Path or URL to video file"
    )

    # Model parameters
    parser.add_argument(
        "--system-prompt",
        default="",
        help="System prompt for the model"
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.6,
        help="Sampling temperature"
    )
    parser.add_argument(
        "--top-p",
        type=float,
        default=0.95,
        help="Top-p sampling parameter"
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=20,
        help="Top-k sampling parameter"
    )
    parser.add_argument(
        "--return-audio",
        action="store_true",
        default=False,
        help="Return audio output"
    )
    parser.add_argument(
        "--no-return-audio",
        action="store_false",
        dest="return_audio",
        help="Don't return audio output"
    )
    parser.add_argument(
        "--enable-thinking",
        action="store_true",
        default=False,
        help="Enable thinking mode"
    )

    args = parser.parse_args()

    # Initialize client (suppress connection messages)
    stdout_backup = sys.stdout
    stderr_backup = sys.stderr
    devnull = open(os.devnull, 'w')
    try:
        sys.stdout = devnull
        sys.stderr = devnull
        client = Client(args.client)
    finally:
        sys.stdout = stdout_backup
        sys.stderr = stderr_backup
        devnull.close()

    # Prepare media inputs
    audio_input = handle_file(args.audio)
    image_input = handle_file(args.image) if args.image else None
    video_input = {"video": handle_file(args.video)} if args.video else None

    # Make prediction
    result = client.predict(
        text=args.text,
        audio=audio_input,
        image=image_input,
        video=video_input,
        history=[],
        system_prompt=args.system_prompt,
        temperature=args.temperature,
        top_p=args.top_p,
        top_k=args.top_k,
        return_audio=args.return_audio,
        enable_thinking=args.enable_thinking,
        api_name="/chat_predict"
    )

    # Extract the LLM's response from the result
    # Result is a tuple: (updates..., messages_list)
    # The last element is the conversation history with the assistant's response
    messages = result[-1]
    llm_response = next(
        (msg['content'] for msg in reversed(messages) if msg.get('role') == 'assistant'),
        None
    )

    if llm_response:
        print(llm_response)
    else:
        print("No response from LLM found")
        print(f"Full result: {result}")


if __name__ == "__main__":
    main()
