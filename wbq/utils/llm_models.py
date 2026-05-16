import logging

import pandas as pd
import streamlit as st
from openai import OpenAI
import ollama
import google.generativeai as genai
from google.generativeai.types.generation_types import GenerationConfig
import dashscope
from dashscope import Generation


from wbq.utils.utils import parse_json_markdown
from wbq.variables import GEMINI_EMBEDDING_MODEL, GPT_EMBEDDING_MODEL, OLLAMA_EMBEDDING_MODEL


logger = logging.getLogger(__name__)


def _raise_provider_error(provider: str, model: str, detail: str) -> None:
    raise RuntimeError(f"{provider} 模型调用失败（{model}）：{detail}")


class QwenModel:
    def __init__(self, api_key, model, system_prompt):
        """
        初始化通义千问模型
        :param api_key: 阿里云 DashScope API Key
        :param model: 模型名称，例如 'qwen-turbo', 'qwen-plus', 'qwen-max'
        :param system_prompt: 系统提示词
        """
        dashscope.api_key = api_key
        self.model = model
        self.system_prompt = system_prompt
        print("============================开始调用QwenModel:=============================")

    def get_response(self, prompt, expecting_longer_output=False, need_json_output=False):
        try:
            # 构建消息列表
            messages = []
            if self.system_prompt.strip():
                messages.append({'role': 'system', 'content': self.system_prompt})

            messages.append({'role': 'user', 'content': prompt})

            # 配置生成参数
            generation_config = {
                'temperature': 0.7,  # 稍微提高一点温度以获得更自然的回答，也可设为 0
                'max_tokens': 4000 if expecting_longer_output else None,
            }

            # 如果需要 JSON 输出，可以在 prompt 中强调，或者使用 qwen-max 支持的 response_format (如果SDK版本支持)
            # 这里采用通用的 prompt 增强方式，因为 dashscope 的 response_format 支持视具体模型版本而定
            if need_json_output:
                # 注意：部分新版本的 qwen 模型支持直接设置 result_format='json'，但为了兼容性，
                # 我们主要依赖 parse_json_markdown 来清洗输出，同时在 prompt 中暗示（可选）
                pass

            response = Generation.call(
                model=self.model,
                messages=messages,
                result_format='message',  # 设置为 message 格式以便处理 role
                **generation_config
            )

            if response.status_code == 200:
                content = response.output.choices[0].message.content.strip()

                if need_json_output:
                    return parse_json_markdown(content)
                else:
                    return content
            else:
                print("================================")
                error_msg = f"Error Code: {response.code}, Message: {response.message}"
                print(error_msg)
                print("================================")
                raise RuntimeError(error_msg)

        except Exception as e:
            logger.exception("Qwen model request failed")
            _raise_provider_error("Qwen", self.model, str(e))

    def get_embedding(self, text, model="text-embedding-v2", task_type="retrieval_document"):
        """
        获取通义千问的 Embedding
        注意：DashScope 的 embedding 接口通常一次处理一个文本或一个列表，返回对应的向量
        :param text: 输入文本 (string) 或 文本列表 (list)
        :param model: 嵌入模型名称，默认 'text-embedding-v2' 或 'text-embedding-v3'
        """
        try:
            # 确保输入是列表格式，因为 API 期望 list
            input_texts = text if isinstance(text, list) else [text]

            # 清理文本中的换行符，类似 ChatGPT 类的处理方式
            input_texts = [t.replace("\n", " ") for t in input_texts]

            response = dashscope.TextEmbedding.call(
                model=model,
                input=input_texts
            )

            if response.status_code == 200:
                embeddings = [item['embedding'] for item in response.output['embeddings']]

                # 如果输入是单个字符串，返回单个向量列表；如果是 DataFrame 处理逻辑，可能需要适配
                # 参照你原有的 Gemini/Ollama 逻辑，如果传入的是用于 DataFrame 处理的逻辑，这里需要调整
                # 假设此处传入的是单个文本用于检索，或者你需要像其他类一样处理 DataFrame

                # 如果调用方传入的是类似 Ollama/Gemini 中的 content (可能是 list of strings)
                if isinstance(text, list):
                    return embeddings
                else:
                    return embeddings[0]
            else:
                print(f"Embedding Error: {response.code}, {response.message}")
                return None

        except Exception as e:
            print("================================")
            print(e)
            print("================================")
            # 如果是在 DataFrame apply 中调用，st.error 可能会报错，需根据上下文调整
            # 这里保持与其他类一致的报错风格，但在 embed_fn 内部调用时需注意 streamlit 上下文
            return None



class ChatGPT:
    def __init__(self, api_key, model, system_prompt):
        if system_prompt.strip():
            self.system_prompt = {"role": "system", "content": system_prompt}
        self.client = OpenAI(api_key=api_key)
        self.model = model
    
    def get_response(self, prompt, expecting_longer_output=False, need_json_output=False):
        user_prompt = {"role": "user", "content": prompt}

        try:
            # TODO: Decide value(temperature, top_p, max_tokens, stop) to get apt response
            completion = self.client.chat.completions.create(
                model=self.model,
                messages = [self.system_prompt, user_prompt],
                temperature=0,
                max_tokens = 4000 if expecting_longer_output else None,
                response_format = { "type": "json_object" } if need_json_output else None
            )

            response = completion.choices[0].message
            content = response.content.strip()
            
            if need_json_output:
                return parse_json_markdown(content)
            else:
                return content
        
        except Exception as e:
            logger.exception("OpenAI model request failed")
            _raise_provider_error("OpenAI", self.model, str(e))
    
    def get_embedding(self, text, model=GPT_EMBEDDING_MODEL, task_type="retrieval_document"):
        try:
            text = text.replace("\n", " ")
            return self.client.embeddings.create(input = [text], model=model).data[0].embedding
        except Exception as e:
            print(e)

class Gemini:
    # TODO: Test and Improve support for Gemini API
    def __init__(self, api_key, model, system_prompt):
        genai.configure(api_key=api_key)
        self.system_prompt = system_prompt
        self.model = model
    
    def get_response(self, prompt, expecting_longer_output=False, need_json_output=False):
        try:
            model = genai.GenerativeModel(
                model_name=self.model,
                system_instruction=self.system_prompt
                )
            
            content = model.generate_content(
                contents=prompt,
                generation_config=GenerationConfig(
                    temperature=0.7,
                    max_output_tokens = 4000 if expecting_longer_output else None,
                    response_mime_type = "application/json" if need_json_output else None
                    )
                )

            if need_json_output:
                result = parse_json_markdown(content.text)
            else:
                result = content.text
            
            if result is None:
                st.write("LLM Response")
                st.markdown(f"```json\n{content.text}\n```")

            return result
        
        except Exception as e:
            logger.exception("Gemini model request failed")
            _raise_provider_error("Gemini", self.model, str(e))
    
    def get_embedding(self, content, model=GEMINI_EMBEDDING_MODEL, task_type="retrieval_document"):
        try:
            def embed_fn(data):
                result = genai.embed_content(
                    model=model,
                    content=data,
                    task_type=task_type,
                    title="Embedding of json text" if task_type in ["retrieval_document", "document"] else None)
                
                return result['embedding']
            
            df = pd.DataFrame(content)
            df.columns = ['chunk']
            df['embedding'] = df.apply(lambda row: embed_fn(row['chunk']), axis=1)
            
            return df
        
        except Exception as e:
            print(e)


class OllamaModel:
    def __init__(self,  model, system_prompt, api_key=None):
        """
        初始化 Ollama 模型

        注意：Ollama 是本地部署的模型，通常不需要 API Key
        api_key 参数保留是为了与其他模型类保持接口一致，实际不使用
        :param api_key: 保留参数，Ollama 不需要（可以传 None 或任意值）
        :param model: 模型名称，例如 'llama3', 'qwen2.5:7b', 'phi3'
        :param system_prompt: 系统提示词
        """
        # Ollama 不需要 API key，但保留参数以统一接口
        self.api_key = api_key
        self.model = model
        self.system_prompt = system_prompt

    def get_response(self, prompt, expecting_longer_output=False, need_json_output=False):
        try:
            # 构建消息列表
            messages = []
            if self.system_prompt.strip():
                messages.append({'role': 'system', 'content': self.system_prompt})

            messages.append({'role': 'user', 'content': prompt})

            # 配置生成参数
            # Ollama 的 options 参数对应生成配置
            options = {
                'temperature': 0.7,  # 稍微提高一点温度以获得更自然的回答
            }

            # 如果需要更长的输出，设置 num_predict（预测的最大 token 数）
            if expecting_longer_output:
                options['num_predict'] = 4000  # Ollama 使用 num_predict 控制最大输出长度

            # 如果需要 JSON 输出，可以在 prompt 中强调，或者使用系统提示增强
            # 部分 Ollama 模型支持 response_format，但这里保持兼容性
            if need_json_output:
                # 可以在 system prompt 中增加 JSON 格式要求
                # 但为了与 QwenModel 风格一致，我们主要依赖 parse_json_markdown 来清洗输出
                pass

            # 调用 Ollama API
            response = ollama.chat(
                model=self.model,
                messages=messages,
                options=options
            )

            if response and 'message' in response:
                content = response['message']['content'].strip()

                if need_json_output:
                    return parse_json_markdown(content)
                else:
                    return content
            else:
                raise RuntimeError("Ollama 返回为空，或返回结果格式不正确。")

        except Exception as e:
            logger.exception("Ollama model request failed")
            _raise_provider_error("Ollama", self.model, str(e))

    def get_embedding(self, text, model=None, task_type="retrieval_document"):
        """
        获取 Ollama 的 Embedding

        Ollama 的 embedding 接口一次处理一个文本，返回对应的向量
        :param text: 输入文本 (string) 或 文本列表 (list)
        :param model: 嵌入模型名称，如果为 None 则使用默认模型（如 'all-minilm'）
        :param task_type: 保留参数，与其他模型类接口保持一致，Ollama 可能不使用
        """
        try:
            # 如果没有指定 embedding 模型，使用默认值
            embedding_model = model if model else "all-minilm"

            # 确保输入是字符串（如果是列表，取第一个或拼接）
            if isinstance(text, list):
                # 如果传入的是列表，可能需要返回多个 embedding
                # 这里为了与 QwenModel 的 get_embedding 保持一致的接口逻辑
                # QwenModel 中如果传入 list，返回 list of embeddings
                embeddings = []
                for t in text:
                    # 清理文本中的换行符
                    t = t.replace("\n", " ")
                    response = ollama.embeddings(
                        model=embedding_model,
                        prompt=t
                    )
                    if response and 'embedding' in response:
                        embeddings.append(response['embedding'])
                    else:
                        print(f"Embedding failed for text: {t[:100]}...")
                        embeddings.append(None)
                return embeddings
            else:
                # 单个字符串，返回单个 embedding
                text = text.replace("\n", " ")
                response = ollama.embeddings(
                    model=embedding_model,
                    prompt=text
                )

                if response and 'embedding' in response:
                    return response['embedding']
                else:
                    print(f"Embedding Error: No embedding in response")
                    return None

        except Exception as e:
            print(f"Ollama Embedding Error: {e}")
            # 如果是在 DataFrame apply 中调用，st.error 可能会报错，需根据上下文调整
            # 这里保持与其他类一致的报错风格
            return None
