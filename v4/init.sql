-- ========================================
-- 公众号AI运营系统 V4 - 数据库初始化
-- ========================================

-- 品牌知识库
CREATE TABLE IF NOT EXISTS brand_knowledge (
    id SERIAL PRIMARY KEY,
    category VARCHAR(50) NOT NULL,  -- enterprise, product, tone, forbidden, prompt
    key VARCHAR(200) NOT NULL,
    value TEXT NOT NULL,
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_brand_category ON brand_knowledge(category);

-- 文章表
CREATE TABLE IF NOT EXISTS articles (
    id SERIAL PRIMARY KEY,
    topic TEXT NOT NULL,
    title VARCHAR(200),
    content TEXT,
    html TEXT,
    summary VARCHAR(500),
    keywords TEXT[],
    quality_score INTEGER,
    status VARCHAR(20) DEFAULT 'draft',  -- draft, published, review, failed
    media_id VARCHAR(100),
    publish_mode VARCHAR(20) DEFAULT 'manual',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 发布日志
CREATE TABLE IF NOT EXISTS publish_logs (
    id SERIAL PRIMARY KEY,
    article_id INTEGER REFERENCES articles(id),
    action VARCHAR(20) NOT NULL,  -- draft, publish, delete
    media_id VARCHAR(100),
    wechat_response JSONB,
    success BOOLEAN DEFAULT false,
    error_msg TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 工作流执行日志
CREATE TABLE IF NOT EXISTS workflow_logs (
    id SERIAL PRIMARY KEY,
    execution_id VARCHAR(100),
    node_name VARCHAR(200),
    step VARCHAR(100),
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    duration_ms INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'success',
    error_msg TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_wf_execution ON workflow_logs(execution_id);
CREATE INDEX idx_wf_node ON workflow_logs(node_name);

-- Prompt 配置
CREATE TABLE IF NOT EXISTS prompts (
    id SERIAL PRIMARY KEY,
    agent_name VARCHAR(50) NOT NULL UNIQUE,  -- industry, user, planning, writing, seo, review
    system_prompt TEXT NOT NULL,
    user_prompt_template TEXT NOT NULL,
    temperature REAL DEFAULT 0.7,
    max_tokens INTEGER DEFAULT 4096,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 插入默认品牌知识
INSERT INTO brand_knowledge (category, key, value, priority) VALUES
    ('enterprise', 'name', '你的品牌名', 1),
    ('enterprise', 'slogan', '你的Slogan', 1),
    ('enterprise', 'industry', '你的行业', 1),
    ('enterprise', 'target_audience', '25-40岁职场人群', 1),
    ('tone', 'style', '专业、深度、亲和', 2),
    ('tone', 'format', '每段不超过4行，适度使用emoji', 2),
    ('forbidden', 'politics', '政治敏感内容', 3),
    ('forbidden', 'false_claim', '虚假承诺、绝对化用语', 3),
    ('forbidden', 'medical', '医疗断言', 3),
    ('product', 'product_a', '产品A - 描述待补充', 2),
    ('product', 'product_b', '产品B - 描述待补充', 2);

-- 插入默认 Prompt
INSERT INTO prompts (agent_name, system_prompt, user_prompt_template) VALUES
    ('industry', '你是资深行业分析师。根据主题和品牌信息，输出行业趋势分析和机会洞察。输出纯JSON。', '主题：{topic}\n品牌：{brand_info}\n输出JSON：{"trends":"...","opportunities":"...","competitors":"..."}'),
    ('user_analysis', '你是用户研究专家。根据品牌定位和主题，输出目标用户画像。输出纯JSON。', '主题：{topic}\n品牌：{brand_info}\n输出JSON：{"persona":"...","pain_points":"...","needs":"..."}'),
    ('planning', '你是资深内容策划。根据行业分析和用户画像，规划文章结构。输出纯JSON。', '主题：{topic}\n行业分析：{industry}\n用户分析：{user}\n输出JSON：{"titles":["..."],"outline":[{"section":"...","point":"...","words":300}],"keywords":["..."]}'),
    ('writing', '你是资深公众号写手。根据结构规划，写出高质量文章（Markdown格式）。', '主题：{topic}\n结构：{outline}\n品牌语气：{tone}\n输出：Markdown格式正文，2000-4000字'),
    ('seo', '你是SEO优化专家。优化文章标题、关键词和摘要。输出纯JSON。', '文章：{content}\n输出JSON：{"title":"...","summary":"...","keywords":["..."]}'),
    ('review', '你是内容质量审核专家。检查文章质量并打分。输出纯JSON。', '文章：{content}\n输出JSON：{"score":1-10,"passed":true/false,"issues":["..."],"suggestions":["..."]}');
