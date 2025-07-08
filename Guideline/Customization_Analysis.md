# RAG 优胜方案工程实践深度剖析

本文档旨在深入剖析 RAG 优胜方案中从PDF解析到最终答案生成的全链路核心技术与工程实践。作者在自述中提到对 `docling` 库进行了“定制化开发”，但通过对代码的细致分析，我们发现这种“定制”并非简单地修改库源码，而是围绕 `docling` 构建了一套精巧、健壮且可扩展的数据处理流水线，并在后续的各个环节中融入了大量提升系统性能和鲁棒性的设计。这体现了卓越的工程设计思想。

---

## 阶段一：解析 (Parsing) - 高质量数据是基石

此阶段的目标是将非结构化的 PDF 文档转换为高质量、结构化的纯文本数据，为后续流程提供干净的“弹药”。

### 实践 1.1：通过精细配置实现 GPU 加速
> **作者自述**: *"利用GPU加速解析过程"*
-   **代码位置**: `src/pdf_parsing.py` -> `PDFParser` 类 -> `_create_document_converter` 方法
-   **核心逻辑**: 作者巧妙地利用了 `docling` 内置的、依赖先进AI模型的处理模式来实现GPU加速。通过设置 `TableFormerMode.ACCURATE`，指示 `docling` 使用计算密集型的 **TableFormer** 模型进行表格识别。这有效地将最耗时的解析任务迁移到 GPU 上，实现了流程的显著加速。

### 实践 1.2：通过后处理增强表格的 LLM 兼容性
> **作者自述**: *"生成HTML格式，实现表格结构的近乎完美转换"* (代码中实现为Markdown)
-   **代码位置**: `src/pdf_parsing.py` -> `JsonReportProcessor` 类 -> `_table_to_md` 方法
-   **核心逻辑**: 鉴于 LLM 更易于理解纯文本，作者设计了一个后处理步骤，利用 `tabulate` 库将 `docling` 解析出的结构化表格数据转换为对 LLM 友好的 Markdown 格式，并用这个清晰的 Markdown 字符串替换掉最终 JSON 中原有的复杂表格对象。

### 实践 1.3：数据规整与丰富
> **作者自述**: *"我……重写了几个方法以适应我的需求，获得了包含解析后所有必要元数据的JSON。"*
-   **代码位置**: `src/pdf_parsing.py` -> `JsonReportProcessor` (`assemble_report`) 和 `PDFParser` (`_normalize_page_sequence`)
-   **核心逻辑**: 这体现在**数据丰富**和**数据清洗**两方面。`JsonReportProcessor` 如同“数据总装车间”，将 `docling` 的零散输出与外部业务元数据（如公司名）组装成完整JSON。`_normalize_page_sequence` 方法则是一个工程严谨性的体现，它通过自动填充空白页来修复原始文档中可能存在的页码不连续问题，确保了数据的规整性。

### 实践 1.4 (荣誉提名)：严谨的实验精神 - 表格序列化
> **作者自述**: *"[尽管序列化潜力巨大]，但获胜的解决方案最终没有使用它……Docling解析表格的效果足够好……增加更多文本反而降低了信噪比。"*
-   **代码位置**: `src/tables_serialization.py`
-   **核心逻辑**: 作者曾投入大量精力研究和实现了一套复杂的**表格序列化**方案，旨在将大表格拆解成LLM易于理解的独立文本块。然而，通过在验证集上的A/B测试，他发现这个功能**反而轻微降低了系统性能**。这个案例充分展示了作者实事求是的工程精神：不迷信任何单一技术，一切以最终效果为准。

---

## 阶段二：注入 (Ingestion) - 构建精准的知识库

此阶段的目标是将解析后的干净文本进行切分、向量化，并构建高效的检索引擎。

### 实践 2.1：“一文一库”的物理隔离架构
> **作者自述**: *"100 databases, where 1 database = 1 document. Because why mix information from all companies into one heap...?"*
-   **核心逻辑**: 这是本项目最核心的架构决策之一。每个报告都拥有一个自己专属的、使用 `text-embedding-3-large` 模型生成的 FAISS 向量数据库。它将检索范围从庞大的混合库缩小到单个目标文档，极大提升了查询相关性，并允许使用 `IndexFlatIP` 这种无需压缩、精度极高的暴力搜索索引。

### 实践 2.2：兼顾精度与上下文的切块策略
> **作者自述**: *"I split the text on each page into chunks of 300 tokens... after finding the top_n relevant chunks, I only use them as pointers to the full page."*
-   **核心逻辑**: 这是一个典型的 **“小块检索，大块喂食”** 策略。
    1.  **小块检索**: 将文本切分为300个token的重叠小块，可以最大化查询与文本块的语义相似度，提升检索精度。
    2.  **大块喂食**: 检索到最相关的Top-N小块后，系统不直接使用它们，而是用其父页面编号作为“指针”，获取完整的父页面作为最终上下文。这确保了LLM拥有最全面的信息。

---

## 阶段三：检索 (Retrieval) - 从知识库中高效淘金

此阶段的目标是从数据库中精准、高效地找出与问题最相关的信息。

### 实践 3.1：LLM 重排序 (Reranking)
> **作者自述**: *"pass text and a question to the LLM and ask, “Is this text helpful for answering the question? How helpful? Rate its relevance from 0 to 1.”"*
-   **代码位置**: `src/reranking.py` 和 `src/prompts.py` (重排提示词)
-   **核心逻辑**: 这是对传统向量检索的巨大升级。在通过向量相似度初步筛选出**Top-30**的页面后，系统会调用廉价高速的LLM（如GPT-4o-mini）作为“二次精排器”。最终排序由向量得分和LLM得分加权平均（`0.3*vec_score + 0.7*llm_score`）得出，并返回**Top-10**的页面。这极大地提升了最终上下文的信噪比。

---

## 阶段四：生成 (Generation) - 打造可靠的答案产线

此阶段的目标是整合检索到的信息，并通过LLM生成精准、合规的最终答案。

### 实践 4.1：三层查询路由 (Multi-level Query Routing)
> **作者自述**: *"Found the name → matched to DB... we only supply the relevant instruction set to the prompt... pass the initial comparison question to the LLM and ask it to create simpler sub-questions."*
-   **核心逻辑**: 设计了一套优雅的级联路由系统，用一系列“廉价”的路由器对问题进行预处理和分发，极大提升了效率和准确性。
    1.  **数据库路由 (Regex)**: 用正则表达式提取公司名，直接定位到对应数据库。
    2.  **提示词路由 (If/Else)**: 根据问题要求的答案类型（数值、布尔等），选择一套专属提示词。
    3.  **复合查询路由 (LLM)**: 当遇到跨公司比较等复杂问题时，用一个LLM先将问题分解为多个简单子问题，分别执行后再汇总。

### 实践 4.2：模块化与版本化的提示词工程
> **作者自述**: *"I store prompts in a dedicated `prompts.py` file, typically splitting prompts into logical blocks..."*
-   **代码位置**: `src/prompts.py`
-   **核心逻辑**: 将提示词作为代码（Prompt-as-Code）进行管理，体现了优秀的软件工程思想。
    1.  **模块化**: 将提示词拆分为系统指令、Schema、One-shot示例、模板等可复用的逻辑块。
    2.  **版本化**: `prompts.py` 文件可以纳入Git进行版本控制，便于追踪变更、协作和回滚。
    3.  **One-shot示例**: 在每个提示中精心设计一个“问题->答案”对，不仅为模型提供了行为范例，还有效校准了模型偏见，并隐式地教会了模型应遵循的JSON结构。

### 实践 4.3：高鲁棒性的结构化输出 (CoT + SO + Reparser)
> **作者自述**: *"I employed a more general approach, providing the model with a single reasoning field... This guarantees that the model always returns valid JSON... If validation fails, the method sends the response back to the LLM, prompting it to conform to the schema."*
-   **核心逻辑**: 这是一个确保LLM输出100%可用、100%合规的“三位一体”黄金组合。
    1.  **CoT (Chain of Thought)**: 设计一个 `reasoning` 字段，引导模型在回答前先进行逻辑思考。
    2.  **SO (Structured Output)**: 使用Pydantic Schema严格限定模型的输出格式。
    3.  **Reparser (容错重试)**: 设计一个后备方案。如果模型返回的JSON未能通过Schema验证，系统会捕获错误，并要求LLM自行“修复”。

---

## 阶段五：评估与迭代 - 系统成功的元实践

这是贯穿所有阶段、确保项目成功的关键保障。

### 实践 5.1：可度量的迭代流程
> **作者自述**: *"I immediately generated a hundred questions and created a validation set from them... By running the system on this set, I monitored how many questions it answered correctly and where it most commonly made mistakes."*
-   **核心逻辑**: 这是最关键但最易被忽视的实践。作者在开发早期就**手动创建了一个验证集**。这个验证集就像一把客观的“尺子”，使得任何对系统（无论是解析、检索还是提示词）的修改，其效果都能被量化评估。这让迭代不再是凭感觉，而是真正的数据驱动，是整个项目能不断优化、最终夺冠的根本原因。

### 实践 5.2：面向性能的系统设计
> **作者自述**: *"I estimated the token consumption per question and processed questions in batches of 25."*
-   **核心逻辑**: 除了在每个环节追求高质量，作者还从系统全局考虑性能。为了充分利用OpenAI API的TPM（Tokens Per Minute）配额，他设计了批量处理机制，将问题以25个为一批并发处理，最终在2分钟内完成了100个问题的回答，展现了卓越的系统工程和性能优化能力。 