# open-domain-qa
This document outlines the steps to build a fast, accurate, and cheap (to build and run) open-domain question answering system that uses Wikipedia articles to answer user queries. Project code is modular to make swapping different document retrieval and processing methods easy. The underlying framework, particularly the retrieval component, can be used with minimal modification for other applications: retrieval augmented generation (RAG) to provide accurate information sources for chatbots, or providing recommendations based on product descriptions and user reviews. An overview of project follows. 

- [Open-Domain Question Answering](#open-domain-question-answering)
- [Data Source: Wikipedia](#data-source-wikipedia)
- [Finding Relevant Documents](#finding-relevant-documents)
  - [Keyword Matching](#keyword-matching)
  - [Embedding Models](#embedding-models)
- [Question Answering](#question-answering)
- [Performance and Benchmarks](#performance-and-Benchmarks)

# Open-Domain Question Answering
Question answering (QA) systems attempt to answer questions posed by a user in natural language.

> Question: How many teeth do dogs have?

> Answer: "42".

QA requires a fairly nuanced understanding of language, and has a variety of practical uses: personal assistants like Siri, handling frequently asked questions in customer support, or providing instant answers in search engines.  This combination of difficult technical challenges and real world applications helped to make QA a staple of natural language processing (NLP) literature. 

We define open-domain question answering (ODQA) as a system that draws from an external knowledge base to answer user queries. For example, we can (and will) use text from Wikipedia articles to answer the question above, e.g., the second paragraph in the article on [dogs](https://en.wikipedia.org/wiki/Dog) contains the text:

> ... powerful jaws that house around 42 teeth ...

Thus, the open-domain QA setting roughly separates into the following components:
1. Information Retrieval (IR) - How do we find relevant documents that will allow us to answer the user's question?
2. Document Processing - How do we process a document's text to find the information needed?
3. (Optional) Reranking answers to incorporate document relevance, answer confidence, etc., for improved performance.

<p align='center'>
<img src="https://github.com/p-mcglaughlin/open-domain-qa/blob/main/images/system.png" width=50% height=50%>
</p>

# Data Source: Wikipedia
Wikipedia articles serve as the QA system's knowledge base. The site regularly provides SQL and XML [database dumps](https://en.wikipedia.org/wiki/Wikipedia:Database_download) containing the text of all ~7 million English Wikipedia articles. A typical file is ~25GB compressed or ~50GB uncompressed. The XML files use html and [wikitext](https://en.wikipedia.org/wiki/Help:Wikitext) markup, making them unsuitable for QA tasks. Code to download and clean Wikipedia dumps is provided in [wiki-reader](wiki-reader). 

This project only extracted plain text. Specifically, we removed:
- Citations, references, external links.
- 'Internal' Wikipedia pages like: Categories, Templates, Help, Special, etc.
- Structured data like infoboxes, tables, and lists.
- **All** markup, including \<math\> and \<code\> blocks. 

In some cases, this removes valuable information. Some of the above items could be preserved, consult [wiki-reader documentation](wiki-reader/README.md) for details.

*Note:* For an alternative open source project to extract Wikipedia text see [attardi/wikiextractor](https://github.com/attardi/wikiextractor).

*Note:* The Hugging Face dataset [wikimedia/wikipedia](https://huggingface.co/datasets/wikimedia/wikipedia) contains a cleaned version of the 11/2023 dump.

# Finding Relevant Documents
Fast and accurate information retrieval methods lie at heart of the open-domain QA system. We consider two types of approaches:
1. Classical IR methods based on keyword matching.
2. Machine learning based vector embeddings.

See the wiki for a more detailed explaination of [keyword matching](https://github.com/p-mcglaughlin/open-domain-qa/wiki/TF%E2%80%90IDF_BM25) and [vector embedding](https://github.com/p-mcglaughlin/open-domain-qa/wiki/Embeddings) approaches. The [approximate nearest neighbors](https://github.com/p-mcglaughlin/open-domain-qa/wiki/Approximate-Nearest-Neighbors) page outlines finding nearest neighbors in high dimensional spaces required for embedding based methods. For a comparison of QA system performance see [Performance and Benchmarks](#performance-and-benchmarks).

*Note:* Sparse encoder methods like SPLADE are an interesting extension for future work.

## Keyword Matching
Classical IR techniques rely on keyword matching. Intuitively, we find documents that frequently use the words appearing in a user's query, and give more weight (importance) to rarer words. 

The term frequency - inverse document frequency ([TF-IDF](https://en.wikipedia.org/wiki/Tf%E2%80%93idf)) heuristic provides a way to weight the importance of matching keywords. The weight for term $t$ in document $d$ is given by:
- **Term frequency** -
  
$$tf(t,d) = \text{ number of times } t \text{ occurs in } d.$$ 

- **Inverse document frequency** - A weighting factor that increases with the rarity of term $t$ across all documents. Let $N$ be the number of documents, and $n(t)$ be the number documents that contain $t$. The inverse document frequency is:

$$idf(t) = \log\bigg(\frac{N}{n(t)}\bigg).$$
- **Term Weight** - $$tf(t,d)\times idf(t).$$

*Note:* TF-IDF is really more a family of algorithms with many [variations](https://nlp.stanford.edu/IR-book/html/htmledition/variant-tf-idf-functions-1.html) on the exact form of $tf$ and $idf$. The most famous of these is BM25 (BM stands for best matching). For a detailed discussion of the BM25 formula see [here](https://www.elastic.co/blog/practical-bm25-part-2-the-bm25-algorithm-and-its-variables).

*Note:* Keyword matching based methods are also refered to as full-text or lexical search.

This project uses [OpenSearch](https://opensearch.org/) to implement BM25 based full-text search. Each Wikipedia article is split into paragraphs, and indexed using the [English analyzer](https://docs.opensearch.org/docs/latest/analyzers/language-analyzers/english/) which removes stop words and performs stemming. User queries are not stemmed since it produces unusual results, see [TF-IDF wiki](wiki/TF-IDF_BM25) for more details and examples.

## Embedding Models
TF-IDF provides a simple and interpretable approach to IR. However, these methods do not 'understand' the user's query, see [TF-IDF wiki](wiki/TF-IDF_BM25) a detailed discussion. Embedding based approaches aim to address this issue by using machine learning models to encode a text's semantic information into a vector (essentially a list of numbers). We can imagine these vectors (or embeddings) as points in some abstract space where similar passages of text are 'close' to each other. To use embeddings for IR, we compute the query's embedding and search for the closests points, see the illustration below. Algorithms for nearest neighbor search are outlined [here](wiki/Approximate-Nearest-Neighbors).

<p align='center'>
<img src="https://github.com/p-mcglaughlin/open-domain-qa/blob/main/images/embedding_example.png" width=40% height=40%>
</p>

The three most common measures of distance or similarity between embeddings $x$ and $y$ are:
- $L^2$: $\lVert x-y \rVert^2 = \sum_i (x_i-y_i)^2$

- dot product: $< x,y > \ = \sum_i x_iy_i $

- cosine: $\frac{<x,y>}{\lVert x \rVert \lVert y \rVert }.$

This project relies on [Sentence Transformers](https://sbert.net/) for embedding models. Refer to the [MTEB leaderboards](https://huggingface.co/spaces/mteb/leaderboard) for a comparison various models available. Tests were conducted using the [Snowflake/snowflake-arctic-embed-s](https://huggingface.co/Snowflake/snowflake-arctic-embed-s) model which provides a good balance between inference speed, embedding size (memory requirements), and retrieval performance. We used cosine similarity in tests since that is how the model was trained. We use vector databases to implement nearest neighbor search. Clients are provied for: [Qdrant](https://qdrant.tech/), [Redis vector sets](https://redis.io/docs/latest/develop/data-types/vector-sets/), [OpenSearch](https://opensearch.org/), and [pgvector](https://github.com/pgvector/pgvector). Extending the (class.py) class is to support other vector database providers is straightforward.

# Question Answering Models
QA systems have a long history in NLP research. One of the most common settings is reading comprehension: answer questions about a passage of text (called the context). Extractive QA models solve these tasks by selecting a substring of the context as the answer. For example:
> Question: Where did the Beatles form?

> Context: The Beatles were an English rock band that formed in ***Liverpool*** in 1960.

Extractive QA models work by outputting two to probability distributions over of tokens in the context paragrpah, one for the start of the answer span and one for the end. Let $p_{start}$ and $p_{end}$ be the respectively probability distributions. Then, the model selects the span corresponding to the pair of indexes $i \leq j$ maximizing: $p_{start}(i)\times p_{end}(j)$. Typically, one builds an extractive QA model by fine-tuning a pretrained model, like [BERT](https://arxiv.org/abs/1810.04805), on standard QA dataset. 

<p align='center'>
<img src="https://github.com/p-mcglaughlin/open-domain-qa/blob/main/images/bert_qa.png" width=30% height=30%>
</p>

The ODQA system uses an extractive QA model to obtain answers from relevant documents found by the IR system. Extractive QA models are rather simple compared to modern LLMs like ChatGPT that people are now accustomed to. This limits the system's ability to answer questions, even when provided with a context paragraph containing the correct answer. For examples, refer to the [Extractive QA wiki](https://github.com/p-mcglaughlin/open-domain-qa/wiki/Extractive-QA). An alternative approach is to run the QA system as retrieval augemented generation (RAG), by feeding relevant documents found by the IR system in the prompt to an LLM.

# Performance and Benchmarks
The following table shows the QA systems performance on the SQuAD dataset. SQuaD is a reading comprehension dataset consisting of 100K   questions about 500 passages of text from Wikipedia. There are a few well-known issues with the dataset.
# Essentially all language models use Wikipedia articles as part of their training data. Since the text passages are Wikipedia articles, the pretrained models have likely seen the answers to many of the questions at training time. 
# Questions were written by crowdsourced workers who were provided paragraphs of text, and instructed to write questions about them. Aw such many questions use the exact phrasing found in the corresponding Wikipedia article. This potentially makes the BM25 method appear more effective than if the users wrote questions, then found paragraphs containing answers.
# Many questions can not be answered without being provided with the original context. For example, 'Which team held the scoring lead throughout the entire game?' 
# Related to the above, the data set was released in 2016, and some answers are now longer factually correct. For example, the correct answer to: "Who was the main performer at this year's halftime show?", in the SQuaD dataset is Coldplay. As of writing this is July 2025, the correct answer is Kendrick Lamar.

Despite the above issues, SQuaD is still typical benchmark to compare ODQA systems. Unlike the original setting, in our tests there is no context provided. Instead, the system must retrieve relevant text passages to serve as the context. The table shows the exact match (EM) and F1 scores for various retrieval methods. BM25 is keyword matching and VEC is an embedding model. EM and F1 are calculated using first answer provided by the system, EM@5 and F1@5 are the best results in the top 5 answers. The +rerank entries used a reranking model.

| Retrieval | EM | F1 | EM@5 | F1@5 |
|-----------|----|----|------|------|
| BM25 | 24.68 | 28.88 | 40.20 | 47.36 |
| VEC | 22.81 | 28.04 | 40.37 | 48.65 |
| BM25+rerank | 31.81 | 36.60 | 40.20 | 47.36 |
| VEC+rerank | 29.74 | 35.04 | 40.37 | 48.65 |
| BM25+VEC+rerank | 36.49 | 41.97 | 49.52 | 57.33 |












