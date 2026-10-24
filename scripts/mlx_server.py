"""Local adapter around pinned MLX-LM 0.32.2, without editing site-packages.

Enforces one pinned model and an exact tokenized 8192 input+output budget.
All generation, Metal kernels, reasoning and tool parsing remain upstream.
"""
import logging,pathlib
from mlx_lm import server
ROOT=pathlib.Path(__file__).resolve().parents[1]
MODEL=ROOT/'models/ornith-mlx'
_tokenize=server.ResponseGenerator._tokenize
_generate=server.ResponseGenerator.generate

def tokenize(self,tokenizer,request,args):
    result=_tokenize(self,tokenizer,request,args)
    count=len(result[0])
    if count+args.max_tokens>8192:
        raise ValueError(f'Local context limit: {count} input + {args.max_tokens} output exceeds 8192')
    logging.info('LAB context input=%s max_output=%s limit=8192',count,args.max_tokens)
    return result

def generate(self,request,generation_args,progress_callback=None):
    selected=generation_args.model.model
    if selected!='default_model' and pathlib.Path(selected).resolve()!=MODEL.resolve():
        raise ValueError('Only the pinned local Ornith model is permitted')
    return _generate(self,request,generation_args,progress_callback)

server.ResponseGenerator._tokenize=tokenize
server.ResponseGenerator.generate=generate
if __name__=='__main__':server.main()
