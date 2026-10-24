"""Local adapter around pinned MLX-LM 0.32.2, without editing site-packages.

Enforces one pinned model and an exact tokenized 8192 input+output budget.
All generation, Metal kernels, reasoning and tool parsing remain upstream.
"""
import logging,pathlib,json,importlib.metadata
from mlx_lm import server
ROOT=pathlib.Path(__file__).resolve().parents[1]
MODEL=ROOT/'models/ornith-mlx'
if importlib.metadata.version('mlx-lm')!='0.32.2':raise RuntimeError('Local adapter requires the verified MLX-LM 0.32.2 version.')
CONTEXT=json.loads((ROOT/'runtimes/profile.json').read_text())['context']
_tokenize=server.ResponseGenerator._tokenize
_generate=server.ResponseGenerator.generate

def tokenize(self,tokenizer,request,args):
    result=_tokenize(self,tokenizer,request,args)
    count=len(result[0])
    if count+args.max_tokens>CONTEXT:
        raise ValueError(f'Maximum context length is {CONTEXT} tokens; requested {count} input + {args.max_tokens} output tokens (context_length_exceeded).')
    logging.info('LAB context input=%s max_output=%s limit=%s',count,args.max_tokens,CONTEXT)
    return result

def generate(self,request,generation_args,progress_callback=None):
    selected=generation_args.model.model
    if selected!='default_model' and pathlib.Path(selected).resolve()!=MODEL.resolve():
        raise ValueError('Only the pinned local Ornith model is permitted')
    return _generate(self,request,generation_args,progress_callback)

server.ResponseGenerator._tokenize=tokenize
server.ResponseGenerator.generate=generate
if __name__=='__main__':server.main()
