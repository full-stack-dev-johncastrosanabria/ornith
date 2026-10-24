"""True MLX prefill/decode rates, fresh KV each repetition; no active server."""
import datetime,json,os,pathlib,statistics,time,uuid
from server import ROOT,LOCK,active
from memory import snapshot,require_space

def main():
    require_space()
    active();fd=os.open(LOCK,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);os.close(fd)
    try:
        import mlx.core as mx
        from mlx_lm import load,stream_generate
        from mlx_lm.sample_utils import make_sampler
        assert mx.default_device()==mx.gpu
        t=time.perf_counter();model,tokenizer=load(str(ROOT/'models/ornith-mlx'));load_s=time.perf_counter()-t;rows=[]
        for i in range(3):
            prompt=tokenizer.apply_chat_template([{'role':'user','content':f'Run {uuid.uuid4().hex}. Write only a Python function that returns the sorted unique integers from a list, with a docstring and three examples.'}],add_generation_prompt=True)
            mx.reset_peak_memory();before=snapshot();t=time.perf_counter();first=None;last=None
            for response in stream_generate(model,tokenizer,prompt=prompt,max_tokens=128,sampler=make_sampler(temp=.6,top_p=.95)):
                require_space()
                if first is None:first=time.perf_counter()-t
                last=response
            row={'repeat':i+1,'wall_s':time.perf_counter()-t,'ttft_s':first,'prompt_tokens':last.prompt_tokens,'generation_tokens':last.generation_tokens,'prefill_tps':last.prompt_tps,'decode_tps':last.generation_tps,'peak_metal_bytes':mx.get_peak_memory(),'memory_before':before,'memory_after':snapshot()};rows.append(row);print(json.dumps({k:v for k,v in row.items() if not k.startswith('memory')}),flush=True)
        p=ROOT/'benchmarks/results'/f"micro-mlx-direct-{datetime.datetime.now().strftime('%Y%m%dT%H%M%S')}.json"
        p.write_text(json.dumps({'schema':1,'runtime':'MLX-LM 0.32.2','metal_device':str(mx.default_device()),'protocol':'native direct stream_generate; one model loaded; fresh KV on every repeat; 128 max tokens; all three repetitions retained including first kernel compilation; not HTTP timing','load_s':load_s,'rows':rows,'medians':{k:statistics.median(x[k] for x in rows) for k in ['prefill_tps','decode_tps','wall_s','ttft_s']}},indent=2)+'\n');print(p)
    finally:LOCK.unlink(missing_ok=True)
if __name__=='__main__':main()
