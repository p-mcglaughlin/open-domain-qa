import tritonclient.http.aio as httpclient
import numpy as np

class Triton_Inference_QA_Client:
    def __init__(self, host: str, port: str, model_name: str, tokenizer):
        '''
        client for triton inference server at host:port
        '''
        self.client = httpclient.InferenceServerClient(url=f'{host}:{port}')
        self.tokenizer = tokenizer
        self.model = model_name
    
    async def answer(self, questions: list[str], contexts: list[str]) -> list[dict]:
        '''
        returns an answer to each question, context pair using extractive question answering
        '''
        tokens = self.tokenizer(questions, contexts, padding='longest', return_tensors='np')
        input_ids = tokens['input_ids']
        attention_mask = tokens['attention_mask']

        m = len(input_ids) # number of questions
        n = len(input_ids[0]) # max length of tokens
        inputs = []
        inputs.append(httpclient.InferInput('input_ids', [m, n], "INT64"))
        inputs.append(httpclient.InferInput('attention_mask', [m, n], "INT64"))
        inputs[0].set_data_from_numpy(input_ids)
        inputs[1].set_data_from_numpy(attention_mask)
    
        outputs = []
        outputs.append(httpclient.InferRequestedOutput('start_logits', binary_data=False))
        outputs.append(httpclient.InferRequestedOutput('end_logits', binary_data=False))
    
        results = await self.client.infer(
            self.model,
            inputs,
            outputs=outputs
        )
        response = results.get_response()

        # post processing to extract results 
        start_logits = np.reshape(response['outputs'][0]['data'], [m, n])
        end_logits = np.reshape(response['outputs'][1]['data'], [m, n])
        results = []
        # for each question, context pair i, find best feasible start and end logits (start <= end)
        # O(number of queries X number of tokens)  
        for i in range(m):
            span_start, span_end, max_sum = 0, 0, start_logits[i][0]+end_logits[i][0]
            idx_max_start = 0
            for j in range(n):
                if attention_mask[i][j] == 0: # end of tokens for this pair
                    break 
                if start_logits[i][j] > start_logits[i][idx_max_start]:
                    idx_max_start = j
                # best feasible pair for end logit j
                opt = start_logits[i][idx_max_start]+end_logits[i][j]
                if opt > max_sum: # found better feasible span start and end
                    max_sum = opt
                    span_start = idx_max_start
                    span_end = j
            ans = self.tokenizer.decode(input_ids[i][span_start: span_end+1])
            start_prob = np.exp(start_logits[i][span_start])/sum(np.exp(start_logits[i]))
            end_prob = np.exp(end_logits[i][span_end])/sum(np.exp(end_logits[i]))
            score = start_prob*end_prob
            results.append({'answer': ans, 'score': score})
        return results 