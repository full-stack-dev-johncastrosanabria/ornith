"""D061 lab adapter around the user's GPT-OSS mlx_api.py (that install is left unmodified).

mlx_api.parse_tool_call rejects a tool name OpenCode did not offer; mlx-lm then drops the call but still
answers finish_reason=tool_calls, so OpenCode sees an empty turn and ends the session (GPT-OSS DEV,
2026-11-20: a call to 'search'). llama.cpp passes any name through and OpenCode answers it with its own
error, letting the model recover; this adapter gives GPT-OSS the same path. Everything else is mlx_api's
own __main__ block, unchanged."""
import json,pathlib,re,sys
from functools import partial
GPTOSS=pathlib.Path.home()/'Developer/gpt-oss-20b-MXFP4-Q8'
sys.path.insert(0,str(GPTOSS))
import mlx_api
from mlx_api import server,mx,OUTPUT_TOKENS,TEMPERATURE,TOP_P,REASONING_EFFORT

original=mlx_api.parse_tool_call
def parse_tool_call(text,tools):
    try:return original(text,tools)
    except ValueError as error:
        if 'is not available' not in str(error):raise
        # Same JSON/format checks, with the requested name treated as offered.
        return original(text,[*tools,{'function':{'name':re.match(r'[\w-]+',text).group()}}])
mlx_api.parse_tool_call=parse_tool_call

assert parse_tool_call('search<|message|>{"q":"x"}',[{'function':{'name':'grep'}}])=={'name':'search','arguments':{'q':'x'}}
assert parse_tool_call('grep<|message|>{"pattern":"x"}',[{'function':{'name':'grep'}}])['name']=='grep'

if __name__=='__main__':
    mx.set_cache_limit(64*1024**2)
    server.ModelProvider=mlx_api.CodingModelProvider
    server.ResponseGenerator=mlx_api.CodingResponseGenerator
    server._run_http_server=partial(server._run_http_server,handler_class=mlx_api.LocalAPIHandler)
    sys.argv[1:1]=['--max-tokens',str(OUTPUT_TOKENS),'--temp',str(TEMPERATURE),'--top-p',str(TOP_P),'--chat-template-args',json.dumps({'reasoning_effort':REASONING_EFFORT})]
    server.main()
