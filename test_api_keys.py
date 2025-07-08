import os
import openai
import google.generativeai as genai
from dotenv import load_dotenv

def test_openai_api():
    """
    Tests the OpenAI API key.
    """
    print("--- 正在测试 OpenAI API Key ---")
    try:
        # 使用从 .env 文件加载的密钥
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # 尝试列出模型作为基本测试
        models = client.models.list()
        
        # 打印一个模型以确认成功
        if models.data:
            print("✅ OpenAI API Key 验证成功！")
            print(f"   成功获取到模型: {models.data[0].id}")
        else:
            print("⚠️ OpenAI API Key 有效，但未能获取到任何模型。")
            
    except openai.AuthenticationError:
        print("❌ OpenAI API Key 验证失败：无效的API Key或权限问题。")
    except Exception as e:
        print(f"❌ 调用 OpenAI API 时发生未知错误: {e}")

def test_gemini_api():
    """
    Tests the Gemini API key.
    """
    print("\n--- 正在测试 Gemini API Key ---")
    try:
        # 配置Gemini API
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        
        # 尝试列出模型作为基本测试
        models = genai.list_models()
        
        # 打印一个模型以确认成功
        model_found = False
        for m in models:
            if 'generateContent' in m.supported_generation_methods:
                print("✅ Gemini API Key 验证成功！")
                print(f"   成功获取到模型: {m.name}")
                model_found = True
                break
        
        if not model_found:
            print("⚠️ Gemini API Key 有效，但未能找到支持'generateContent'的模型。")

    except Exception as e:
        # Gemini的Python SDK可能会以多种方式抛出异常，捕获通用异常
        print(f"❌ Gemini API Key 验证失败或调用时发生错误: {e}")

if __name__ == "__main__":
    # 加载 .env 文件中的环境变量
    if not load_dotenv():
         print("警告：未能找到 .env 文件。请确保该文件存在于项目根目录。")
         # 即使没有.env文件，也尝试从环境中直接读取
    
    # 检查密钥是否存在
    openai_key = os.getenv("OPENAI_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")

    if not openai_key:
        print("未找到 OPENAI_API_KEY 环境变量。")
    else:
        test_openai_api()

    if not gemini_key:
        print("\n未找到 GEMINI_API_KEY 环境变量。")
    else:
        test_gemini_api() 