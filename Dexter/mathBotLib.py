# Before running this script:
# pip install gradio openai

import argparse
import asyncio
from pathlib import Path
from typing import Optional

import gradio as gr
from openai import AsyncOpenAI

from usage import print_usage, format_usage_markdown
from chroma_db import query_textbook


class ChatAgent:
    def __init__(
        self,
        model: str,
        prompt: str,
        show_reasoning: bool,
        reasoning_effort: str | None,
        collection_name: Optional[str] = None,
        chapter: Optional[str] = None,
        db_path: Optional[str] = None,
        top_k: int = 3
    ):
        self._ai = AsyncOpenAI()
        self.model = model
        self.show_reasoning = show_reasoning
        self.reasoning = {}
        if show_reasoning:
            self.reasoning['summary'] = 'auto'
        if 'gpt-5' in self.model and reasoning_effort:
            self.reasoning['effort'] = reasoning_effort

        self.usage = []
        self.usage_markdown = format_usage_markdown(self.model, [])

        # Database parameters
        self.collection_name = collection_name
        self.chapter = chapter
        self.db_path = db_path
        self.top_k = top_k
        self.use_rag = collection_name is not None

        self._history = []
        self._prompt = prompt
        if prompt:
            self._history.append({'role': 'system', 'content': prompt})

    def _augment_with_rag(self, user_message: str) -> str:
        """Query the textbook database and augment the message with relevant context."""
        if not self.use_rag:
            return user_message
        
        try:
            results = query_textbook(
                collection_name=self.collection_name,
                query_text=user_message,
                chapter=self.chapter,
                top_k=self.top_k,
                persist_dir=self.db_path
            )
            
            # Build context from results
            context_parts = []
            if results['documents'] and results['documents'][0]:
                context_parts.append("Relevant textbook content:")
                context_parts.append("-" * 50)
                for doc, metadata in zip(results['documents'][0], results['metadatas'][0]):
                    context_parts.append(f"[{metadata.get('section', 'Unknown')} - {metadata.get('subsection', 'Unknown')}]")
                    context_parts.append(doc)
                    context_parts.append("-" * 50)
                
                context = "\n".join(context_parts)
                augmented_message = f"{user_message}\n\nContext from textbook:\n{context}"
                return augmented_message
        except Exception as e:
            print(f"Warning: Failed to query database: {e}")
        
        return user_message

    async def get_response(self, user_message: str):
        # Augment user message with textbook context if RAG is enabled
        augmented_message = self._augment_with_rag(user_message)
        self._history.append({'role': 'user', 'content': augmented_message})

        stream = self._ai.responses.stream(
            input=self._history,
            model=self.model,
            reasoning=self.reasoning,
        )
        async with stream as stream:
            async for event in stream:
                if event.type == "response.output_text.delta":
                    yield 'output', event.delta

                if event.type == "response.reasoning_summary_text.delta":
                    yield 'reasoning', event.delta

            response = await stream.get_final_response()
            self.usage.append(response.usage)
            self.usage_markdown = format_usage_markdown(self.model, self.usage)
            self._history.extend(
                response.output
            )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print_usage(self.model, self.usage)


async def _main_console(agent_args):
    with ChatAgent(**agent_args) as agent:
        while True:
            message = input('User: ')
            if not message:
                break

            reasoning_complete = True
            if agent.show_reasoning:
                print(' Reasoning '.center(30, '-'))
                reasoning_complete = False

            async for text_type, text in agent.get_response(message):
                if text_type == 'output' and not reasoning_complete:
                    print()
                    print('-' * 30)
                    print()
                    print('Agent: ')
                    reasoning_complete = True

                print(text, end='', flush=True)
            print()
            print()


def _main_gradio(agent_args):
    # Constrain width with CSS and center
    css = """
    /* limit overall Gradio app width and center it */
    .gradio-container, .gradio-app, .gradio-root {
      width: 120ch;
      max-width: 120ch !important;
      margin-left: auto !important;
      margin-right: auto !important;
      box-sizing: border-box !important;
    }
    
    #reasoning-md {
        max-height: 300px;
        overflow-y: auto;
    }
    """

    reasoning_view = gr.Markdown('', elem_id='reasoning-md')
    usage_view = gr.Markdown('')

    mathjax_script = """
    <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"></script>
    <script>
    MathJax = {
      tex: {
        inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
        displayMath: [['$$', '$$'], ['\\\\[', '\\\\]'], ['[', ']']],
        processEscapes: true
      },
      svg: {
        fontCache: 'global'
      },
      startup: {
        pageReady: async () => {
          await MathJax.typesetPromise();
          const observer = new MutationObserver(async (mutations) => {
            await MathJax.typesetPromise();
          });
          observer.observe(document.body, { childList: true, subtree: true });
          return MathJax.startup.defaultPageReady();
        }
      }
    };
    </script>
    """

    with gr.Blocks(css=css, theme=gr.themes.Monochrome(), head=mathjax_script) as demo:
        agent = gr.State()

        async def get_response(message, chat_view_history, agent):
            output = ""
            reasoning = ""

            async for text_type, text in agent.get_response(message):
                if text_type == 'reasoning':
                    reasoning += text
                elif text_type == 'output':
                    output += text
                else:
                    raise NotImplementedError(text_type)

                yield output, reasoning, agent.usage_markdown, agent

            yield output, reasoning, agent.usage_markdown, agent

        with gr.Row():
            with gr.Column(scale=5):
                bot = gr.Chatbot(
                    label=' ',
                    height=600,
                    resizable=True,
                )
                chat = gr.ChatInterface(
                    chatbot=bot,
                    fn=get_response,
                    additional_inputs=[agent],
                    additional_outputs=[reasoning_view, usage_view, agent]
                )

            with gr.Column(scale=1):
                reasoning_view.render()
                usage_view.render()

        demo.load(fn=lambda: ChatAgent(**agent_args), outputs=[agent])

    demo.launch()


def main(
    prompt_path: Path,
    model: str,
    show_reasoning,
    reasoning_effort: str | None,
    use_web: bool,
    collection_name: Optional[str] = None,
    chapter: Optional[str] = None,
    db_path: Optional[str] = None
):
    agent_args = dict(
        model=model,
        prompt=prompt_path.read_text() if prompt_path else '',
        show_reasoning=show_reasoning,
        reasoning_effort=reasoning_effort,
        collection_name=collection_name,
        chapter=chapter,
        db_path=db_path,
        top_k=3
    )

    if use_web:
        _main_gradio(agent_args)
    else:
        asyncio.run(_main_console(agent_args))


# Launch app
if __name__ == "__main__":
    parser = argparse.ArgumentParser('ChatBot')
    parser.add_argument('prompt_file', nargs='?', type=Path, default=None)
    parser.add_argument('--web', action='store_true')
    parser.add_argument('--model', default='gpt-5-nano')
    parser.add_argument('--show-reasoning', action='store_true', default=True)
    parser.add_argument('--reasoning-effort', default='low')
    parser.add_argument('--collection', default='chapter-1-functions', help='Chroma collection name for RAG')
    parser.add_argument('--chapter', default=None, help='Filter results by chapter')
    parser.add_argument('--db-path', default='./chroma_db_persistent', help='Path to Chroma database')
    args = parser.parse_args()
    main(
        args.prompt_file,
        args.model,
        args.show_reasoning,
        args.reasoning_effort,
        args.web,
        collection_name=args.collection,
        chapter=args.chapter,
        db_path=args.db_path
    )
