import re, os

base = os.path.expanduser('~/github/sites')
tmpl_path = os.path.join(base, 'ai-weekly-report-2026-08-12.html')
out_path = os.path.join(base, 'ai-weekly-report-2026-08-26.html')

tmpl = open(tmpl_path, 'r', encoding='utf-8').read()
css_m = re.search(r'<style>.*?</style>', tmpl, re.S)
if not css_m:
    raise RuntimeError('CSS not found')
css = css_m.group(0)

def card(icon, title, body, source):
    return f'''<div class="card">
            <div class="card-icon">{icon}</div>
            <h3>{title}</h3>
            <p>{body}</p>
            <div class="source">来源：{source}</div>
        </div>'''

def section_start(secid, title, intro):
    return f'''<section class="section" id="{secid}">
    <h2>{title}</h2>
    <p class="section-intro">{intro}</p>'''

def section_end():
    return '</section>'

def cards_grid(cards):
    return '<div class="card-grid">\n' + '\n'.join(cards) + '\n</div>'

def highlight(text):
    return f'''<div class="highlight">
    <p>{text}</p>
</div>'''

def quote(text):
    return f'''<div class="quote">
    <strong>竞争格局判断：</strong>{text}
</div>'''

def model_box(items):
    inner = '\n'.join(f'<div class="model-item"><strong>{k}：</strong>{v}</div>' for k,v in items)
    return f'''<div class="model-box">
    <h3>M365 Copilot 企业价值速览</h3>
    {inner}
    <div class="source">来源：Microsoft Learn / Microsoft 365 Blog / 公开报道</div>
</div>'''

def table(rows):
    header = rows[0]
    body = rows[1:]
    th = ''.join(f'<th>{h}</th>' for h in header)
    trs = ''
    for r in body:
        trs += '<tr>' + ''.join(f'<td>{c}</td>' for c in r) + '</tr>'
    return f'''<div class="table-wrapper">
    <table>
        <tr>{th}</tr>
        {trs}
    </table>
</div>'''

# ---- Sections ----
sec1 = section_start('sec1', '一、AI Agent 前沿动态', '本周 AI Agent 的核心叙事是“协议共治 + 真实世界落地 + 合规前置”。8 月 20 日，Google 的 A2A 协议正式加入由 Linux Foundation 指导的 Agentic AI Foundation，与 Anthropic 发起的 MCP 共享同一治理框架；同日 Binance 推出 Agent OS，让 AI Agent 首次大规模连接真实金融基础设施。欧盟 AI 法案 Article 50 已于 8 月 2 日全面执行，AI 互动披露、合成内容水印与深度伪造标签成为硬性要求。对企业而言，Agent 不再只是技术 Demo，而是必须接受权限、审计、成本与合规约束的“数字员工”。')
sec1_cards = [
    card('🔗', 'Google A2A 加入 Agentic AI Foundation，MCP/A2A 进入同一治理框架',
         '8 月 20 日，Google 的 Agent2Agent 协议正式加入由 Linux Foundation 指导的 Agentic AI Foundation，该基金会已托管 Anthropic 的 MCP。MCP 解决“Agent 如何调用工具与数据”的垂直集成问题，A2A 解决“Agent 如何相互发现与委托”的水平协作问题。两者共治意味着企业 Agent 互操作性从“协议战争”转向“分层标准”，降低被单一厂商锁定的风险。',
         'aitechconnect.in / Axios 2026-08-20'),
    card('💱', 'Binance 推出 Agent OS：AI Agent 可交易、支付与投资',
         'Binance 于 8 月 20 日推出 Agent OS，通过 MCP 服务器将其交易、市场数据、钱包与支付 API 开放给 ChatGPT、Claude Code、Codex 等 AI 客户端。用户需为 Agent 设立独立子账户、手动注资、默认禁止提现，并对交易额度设限。这标志着 Agent 首次大规模进入“管理真实资金”的场景，对制造业企业的启示是：任何具备执行权限的 Agent 都必须先解决资金/设备/系统的隔离与审批。',
         'TechCrunch / Particle.news 2026-08-20'),
    card('⚖️', '欧盟 AI 法案 Article 50 于 8 月 2 日全面执行',
         '欧盟 AI 法案透明度条款正式生效：所有与用户交互的聊天机器人/智能体必须清晰披露其为 AI；AI 生成的音频、图像、视频、文本必须嵌入机器可读水印；深度伪造内容必须标注。违规最高可罚 1500 万欧元或全球年营收 3%。已在市场流通的系统须在 2026 年 12 月 2 日前补齐水印能力。',
         'EU AI Act / the-agent-report.com 2026-08'),
    card('🔏', 'Anthropic 为 Claude 全文本嵌入不可见水印',
         '为配合欧盟透明度要求，Anthropic 宣布未来 Claude 模型将对生成文本嵌入不可见、机器可读的水印，并为图片/文件附加 C2PA 来源元数据。水印不影响文本质量，但能经受复制粘贴和轻度编辑。企业若将 Claude/Copilot 生成内容用于对外材料，需建立内容溯源与合规审查流程。',
         'Anthropic 官方 / artificialintelligenceact.substack.com 2026-08'),
    card('🛡️', 'OpenAI 转而支持加州 SB 53，前沿实验室遏制失控模型计划不足',
         'OpenAI 在致加州州长的信中转变立场，支持强化 AI 安全法案 SB 53；同时 Guidelight AI Standards 研究显示，Anthropic、Google、Meta、OpenAI、xAI 等前沿实验室在遏制潜在失控模型方面普遍缺乏具体计划。JustSayAI 早报亦指出，约五分之一企业无法实时阻止失控 AI Agent 的支出。企业部署 Agent 前必须完成权限、预算、护栏与审计设计。',
         'TechCrunch / JustSayAI 2026-08-21/23'),
    card('🏭', 'DeepSeek Harness：一座“造 Agent 的工厂”',
         'JustSayAI 博客将 DeepSeek Harness 比喻为“造车工厂的生产线”而非“整车”：它系统性解决底层配件组装逻辑，让开发者用模块化方式拼装 Agent。Codex 提供的是即用型整车，DSH 提供的是产线。对企业 IT 负责人而言，这意味着 Agent 开发门槛下降，但治理复杂度上升——必须同时管理平台、工具链与输出可靠性。',
         'JustSayAI 博客 2026-08-21'),
]
sec1 += cards_grid(sec1_cards) + highlight('<strong>高管视角：</strong>本周 Agent 生态发生三重质变：A2A/MCP 共治让互操作有章可循，Binance Agent OS 让 Agent 开始管理真实资产，欧盟 AI 法案让透明度成为合规底线。汽车/制造企业在引入 Agent 时，应把“身份权限最小化、操作全程审计、沙箱/子账户隔离、预算硬上限、人工复核节点”作为前置条件，而非事后补丁。') + section_end()

sec2 = section_start('sec2', '二、M365 Copilot 新闻、功能更新与企业案例', '本周 M365 Copilot 的核心动向是“Agentic 工作流正式计费 + 控制平面完善 + 安全治理升级”。Copilot Cowork 在 6 月 16 日 GA 后，7 月 1 日起进入按量计费；Agent 365 作为 Agent 控制平面已于 5 月 1 日 GA；Work IQ 成为贯穿 M365 的统一智能层。CIO 在享受 Agent 自动化红利的同时，必须同步建立成本管理、数据治理与合规体系。')
sec2_cards = [
    card('💳', 'Copilot Cowork GA 并启用按量计费',
         'Copilot Cowork 于 2026 年 6 月 16 日全球正式上线，采用 Copilot Credits 按量计费：Pay-as-you-go 为 0.01 美元/Credit，P3 预购方案根据 30 万至 3 亿 Credit 量级提供 5%–20% 折扣。典型任务成本：轻量 0.7–2 美元、中等 4–6 美元、重度约 15 美元。企业需在 M365 管理中心配置消费策略、预算与告警，避免“惊喜账单”。',
         'Microsoft 365 Blog / Microsoft Learn 2026-08'),
    card('🎛️', 'Agent 365 控制平面 GA：企业级 Agent 治理中枢',
         'Agent 365 于 2026 年 5 月 1 日 GA，约 15 美元/用户/月。它提供 Agent 注册表、Entra ID 身份与访问控制、Agent 活动可视化、跨 Agent 互操作与企业级安全。对汽车/制造企业而言，Agent 365 是把“ Wild West 式 Agent 试点”升级为“可治理生产环境”的关键控制平面。',
         'Microsoft 365 Blog / LinkedIn 2026-03/05'),
    card('🧠', 'Work IQ 与 M365 Copilot Wave 3：统一智能层',
         'M365 Copilot Wave 3 强调从“辅助”到“Agentic”的转变：Work IQ 作为工作场所智能层，连接邮件、文件、会议与协作关系，为 Copilot 与 Agent 提供上下文；Copilot Cowork 则基于 Work IQ 在 Outlook、Excel、PowerPoint、Teams 中执行多步骤任务。微软提出的 Frontier Transformation 认为，AI 目标不应止于效率，而应转化为新增长动能。',
         'Microsoft 365 Blog / Empowering.Cloud 2026-08'),
    card('📱', 'Copilot 整合为统一“超级 App”，Autopilot 代理层级浮现',
         '微软继续推进将 Windows Copilot、M365 Copilot、Edge Copilot 等整合为一款统一应用，并计划推出更高阶的 Autopilot 层级，让 AI 在更少人工干预下完成跨应用工作流。同时 Copilot 将于 2026 年 8 月支持 Outlook Classic，降低大型制造企业迁移阻力。',
         'GCN / MSN / Microsoft 365 路线图 2026-08'),
    card('🔐', 'M365 Copilot 安全与合规：Domain Exclusion 撤回与漏洞披露',
         '微软此前预告的 Domain Exclusion 功能（限制 Copilot Web Grounding 来源）发布后迅速撤回，原因未明；安全研究者披露 Copilot 存在诱导泄露敏感资料与 2FA 窃取风险。提醒企业在启用 Cowork 前必须完成 Purview 数据分类、DLP、敏感度标签、条件访问、审计日志与钓鱼演练。',
         'heise online / 公开安全报道 2026-08'),
    card('🏭', 'KPMG 与微软规模化部署可信企业 Agent',
         'KPMG 与微软宣布在全球范围内通过 Agent 365 与 Microsoft 365 Copilot 规模化部署可信企业 AI 代理，强调治理、合规与可审计性。这为汽车零部件企业从咨询、架构到落地提供了参考范式。',
         'KPMG / Microsoft 官方公告 2026-08'),
]
sec2 += cards_grid(sec2_cards) + model_box([
    ('Cowork 计费要点', '需 M365 Copilot 订阅（$30/用户/月）作为前提；Cowork 用量单独按 Credit 计费，租户级共享额度；可用 P3 预购或 PAYG。'),
    ('汽车行业高价值场景', 'APQP/PPAP 文档协同、全球供应商技术邮件、多语言会议纪要、售后索赔分析、质量报告自动生成。'),
    ('治理优先级', '在开启 Cowork 前完成：计费策略、消费预算、敏感度标签、DLP、Entra 访问组、审计日志、人工审批节点。')
]) + section_end()

sec3 = section_start('sec3', '三、汽车零部件行业 AI 应用落地', '本周汽车行业 AI 的核心叙事是“物理 AI + 智驾 + 机器人”共振。VLA 与世界模型加速融合，小鹏、华为、蔚来、地平线、Momenta 等推动智驾进入物理 AI 阶段；人形机器人自进化迭代催化汽零赛道，线控底盘、域控制器、热管理与 AI 服务器液冷成为新增量。对传统零部件制造，视觉质检、预测性维护、智能排产仍是高 ROI 落地抓手。')
sec3_cards = [
    card('🚗', '物理 AI 重塑智驾：VLA + 世界模型成为主流路线',
         '2026 年，特斯拉 FSD V14 集成 xAI Grok 大模型并利用世界模型进行数据生成与闭环仿真；小鹏 X-Mind 将预测性世界模型内嵌为 VLA 视觉思维链；华为 ADS 5.0 搭载 WEWA 2.0，云端引入 Multi-Agent 群体博弈；蔚来 NWM、Momenta R7、地平线 HSD V2.0 均采用世界模型 + 端到端强化学习。黑芝麻智能 CEO 单记章认为：VLA + 世界模型是智驾未来最有可能的技术路线。',
         '钛媒体 / 新浪财经 2026-08'),
    card('🤖', '人形机器人自进化提速，汽零赛道受益',
         '宇树科技董事长王兴兴表示，公司正推动物理 AI 机器人模型自进化：利用前沿 AI 大模型在设定规则、经验、约束和工具基础上，自主检索论文与开源方案，生成机器人控制代码并在仿真/实物上部署测试。上海证券指出，中国在人形机器人供应链完整度、成本控制和快速量产上优势明显；汽零企业的精密加工与量产能力是机器人成本下探的核心支撑。',
         '东方财富 / 界面新闻 2026-08-20'),
    card('🏆', '2026 全球汽车零部件 TOP100：中国企业数量超越美、德',
         '2026 年全球汽车零部件百强榜单显示，中国企业数量已超过美国、德国。AI、智驾与出海能力成为零部件企业提升全球排名的核心变量；未能实现 AI 赋能的传统供应商将在成本战中进一步承压。',
         '行业公开报道 2026-08'),
    card('⚙️', '线控底盘与域控制器：从机械件到智能执行器',
         '浙江世宝定增近 14 亿元投向线控转向；卓驭科技展示全栈移动物理 AI 智驾方案。物理 AI 正把汽车零部件从“机械件”升级为“智能执行器”，线控底盘、智能悬架、热管理系统与边缘计算平台迎来新一轮订单周期。',
         '公开行业资讯 2026-08'),
    card('🏭', '工业 AI 仍需“懂制造”：从场景积累到商业化',
         '工业 AI 的核心门槛不是模型参数，而是制造场景 Know-how。卡奥斯等平台通过缺陷样本、工艺参数到设备机理的数据闭环形成飞轮。汽车零部件企业在引入视觉质检、预测性维护时，应优先与具备行业经验的平台合作。',
         '行业公开报道 2026-08'),
    card('💼', 'M365 Copilot 在汽车零部件企业的高价值场景',
         '某国内汽车零部件集团试点 M365 Copilot 后，技术文档撰写效率提升 30–50%，会议纪要整理时间减少 60%，Excel 数据分析门槛显著降低。建议优先赋能项目经理、质量工程师、采购工程师与售后工程师。',
         '微软企业 AI 案例 / 行业观察'),
]
sec3 += cards_grid(sec3_cards)
sec3 += '<h3>高 ROI 落地场景优先级</h3>'
sec3 += table([
    ['优先级', '场景', '适用技术', '预期收益'],
    ['<span class="status status-success"><span class="status-dot"></span>高</span>', '视觉质检', '计算机视觉 + 缺陷检测', '漏检率降 40–60%，年省数十万至数百万'],
    ['<span class="status status-success"><span class="status-dot"></span>高</span>', '预测性维护', '时序预测 + 传感器数据', '非计划停机降 20–30%，维护成本降 15–25%'],
    ['<span class="status status-success"><span class="status-dot"></span>高</span>', '智能排产', '运筹优化 + 强化学习', '产能利用率提升 15–20%，交付周期缩短 10–15%'],
    ['<span class="status status-accent"><span class="status-dot"></span>中</span>', '办公效率提升', 'M365 Copilot + 知识库', '文档/会议/数据分析效率提升 30–50%'],
    ['<span class="status status-accent"><span class="status-dot"></span>中</span>', '车载 AI/智能座舱', '车载大模型 + 边缘推理', '提升用户体验，带动 Tier1 软硬件订单'],
    ['<span class="status status-warning"><span class="status-dot"></span>待观察</span>', '生成式 AI 研发设计', 'CAD/CAE 集成、生成式设计', '长期潜力大，短期需验证数据与合规'],
])
sec3 += highlight('<strong>落地路径建议：</strong>第一阶段（1–3 个月）选择 1–2 个高 ROI 制造场景试点；第二阶段（3–6 个月）扩展至多产线并建立 MLOps；第三阶段（6–12 个月）沉淀为平台能力，同步部署 M365 Copilot 与车载 AI 接口；长期建立 AI 治理体系（安全、合规、数据隐私、模型可审计）。') + section_end()

sec4 = section_start('sec4', '四、大模型竞争与产业格局', '本周大模型竞争呈现“国产模型以成本与调用量领跑、海外巨头模型迭代与人才地震并行、英伟达全栈布局加速”的格局。DeepSeek V4 Pro 转正并上线视觉模型，智谱 GLM-5.3 以低价 API 亮相，xAI Grok 4.6 降价登顶智能体榜单；OpenAI GPT-5.6 成为 M365 Copilot 首选模型；Google DeepMind 高层持续变动；英伟达发布 LTX-2.5 世界模型、Nemotron 3.5 与 5000 亿美元 AI 融资平台。')
sec4_cards = [
    card('🇨🇳', 'DeepSeek V4 Pro 转正，V4-Flash-Vision-Exp 上线',
         'DeepSeek V4 Pro 正式结束测试并全量上线，支持 100 万 Token 超长上下文与 384K 输出长度，Agent 能力显著增强。8 月 21 日 DeepSeek 无预警上线实验性多模态模型 DeepSeek-V4-Flash-Vision-Exp，补齐视觉短板。JustSayAI 评论其 API 定价形成“斩杀线”，第三方本地部署无利可图。',
         'JustSayAI / 知乎 2026-08-21/22'),
    card('🧮', '智谱 GLM-5.3 API 上线，xAI Grok 4.6 降价登顶',
         '智谱 AI 发布 GLM-5.3，API 定价低至 1.4 美元/百万 Token，Max 版本基准测试表现卓越；xAI 发布 Grok 4.6，在主流智能体能力评测中取得 1753 分超越 Fable 5 登顶，API 定价约为同类旗舰的一半。国产与国际模型在“低成本 + 高 Agent 能力”赛道正面交锋。',
         'fxbaogao.com / JustSayAI 2026-08-19/14'),
    card('🚀', 'OpenAI GPT-5.6 成为 M365 Copilot 首选模型',
         'OpenAI 宣布 GPT-5.6 成为 Microsoft 365 Copilot 在 Word、Excel、PowerPoint、Chat 和 Cowork 中的新首选模型。对企业客户而言，这意味着更强的推理、编码与多步骤任务能力，同时也需关注模型版本升级带来的变更管理与安全评估。',
         'OpenAI 官方 / Microsoft 365 Blog 2026-08'),
    card('🌊', 'Google DeepMind 高层地震，Gemini 3.7 Flash 与 Genie 3 发布',
         'Google DeepMind 持续高层变动：Jeff Dean 离职、Demis Hassabis 传出走或转任 Alphabet 首席科学家；同时 Google 发布 Gemini 3.7 Flash，编码基准升至 43.6%，并推出 Genie 3 实时交互式通用世界模型。人才流动与技术路线调整值得持续观察。',
         'JustSayAI / AI Conference London 2026-08'),
    card('🎨', '英伟达全栈布局：LTX-2.5、Nemotron 3.5、5000 亿美元融资平台',
         'NVIDIA 发布开放权重世界模型 LTX-2.5，将视频制作技术栈压入单机；同步推出 Nemotron 3.5 Lightning 与 NeMo Switchyard 智能路由库，按请求难度动态选择模型以降低推理成本。英伟达还与阿波罗、贝莱德等合作，计划撬动超 5000 亿美元第三方资本投入 AI 基础设施。',
         'JustSayAI / MarkTechPost 2026-08'),
    card('📈', '中国 AI 大模型调用量全球第一',
         '央视网等报道，中国 AI 大模型调用量已连续多周保持全球第一，多个国产模型接连迭代“上新”，海外游戏工作室和电商平台积极接入中国开源模型。2026 年以来中国 AI 正持续向全球赋能。',
         '央视网 / fxbaogao.com 2026-08'),
]
sec4 += cards_grid(sec4_cards) + quote('大模型竞争正从“参数规模 + 榜单分数”转向“成本效率 + 可用性 + 生态锁定 + 合规可信”。国产模型在 ToB 落地、Token 成本、开源可控上优势明显；海外闭源模型在企业级安全、合规、多模态工具链上领先。企业选型应回归业务结果，避免为“排队资格”支付溢价。') + section_end()

sec5 = section_start('sec5', '五、中文 AI 创作者/资讯源精选', '本章整合 JustSayAI 早晚报（2026-08-19 至 2026-08-25）与人民公园说 AI 播客/博客核心观点，作为中文独立视角呈现。')
sec5_cards = [
    card('🤖', '8 月 22 日早报：英伟达证明系统框架比模型更关键，DeepSeek 发布视觉模型',
         '英伟达最新研究指出智能体系统框架的重要性已超越底层模型；DeepSeek 紧跟着发布视觉模型冲击智能体基准；Gemma 下载破十亿印证开源生态正加速涌入 Agent 赛道。',
         'JustSayAI 2026-08-22 早报'),
    card('💱', '8 月 20 日早报：Stripe 75 亿美元收购 OpenRouter，AI 泡沫缓慢泄气？',
         'Stripe 以 75 亿美元收购 OpenRouter 点燃 AI 支付整合潮；Rillet 48 小时融资跻身独角兽；《华尔街日报》认为行业泡沫正缓慢泄气而非破裂。AI 基础设施整合与估值预期正在分化。',
         'JustSayAI 2026-08-20 早报'),
    card('🛠️', '8 月 19 日早报：阿里玄铁 C950 跑通通义千问 27B，亚马逊 AgentCore 支付上线',
         '阿里巴巴玄铁 C950 跑通大模型端侧部署；亚马逊 AgentCore 支付功能正式上线；WhiteFiber 巨额融资扩建数据中心。AI 硬件突破与商业落地同步加速。',
         'JustSayAI 2026-08-19 早报'),
    card('🏭', '8 月 18 日：Cursor 推出 Origin 代码托管，Copilot 自动修复引发 Jira 入侵',
         'Cursor 推出 Origin 代码托管平台；AI 安全漏洞事件显示 Copilot 自动修复功能可能触发 Jira 入侵风险。提示企业：Agent 的自动化能力必须与最小权限、变更审批与审计日志配套。',
         'JustSayAI 2026-08-18 早晚报'),
    card('🏭', '博客：99% 的人不配用它｜DeepSeek Harness 是一座造 Agent 的工厂',
         'JustSayAI 认为 DeepSeek Harness 不是普通工具更新，而是“造车工厂的生产线”：它系统性解决底层配件组装逻辑，让开发者模块化拼装 Agent。对企业 IT 负责人而言，这意味着 Agent 开发门槛下降，但治理复杂度上升。',
         'JustSayAI 博客 2026-08-21'),
    card('🚗', '博客：智驾的终局是物理 AI，L4 可能比 L3 更快？',
         '人民公园说AI 对话千里智驾 CTO 杨沐指出，端到端 + BEV 已触及瓶颈，L3 人机共驾责任边界难以清晰；L4 通过限定场景与系统冗余可能更快实现商业化。对 Tier 1 与主机厂的投资节奏具有重要参考价值。',
         'JustSayAI 博客 2026-07-24'),
]
sec5 += cards_grid(sec5_cards)
sec5 += '<div class="source">订阅渠道：JustSayAI 早晚报 https://www.justsayai.org/ | 人民公园说AI 播客/YouTube/B 站 | JustSayAI 博客 https://www.justsayai.org/blog</div>' + section_end()

sec6 = section_start('sec6', '六、总结与下周观察重点', '')
sec6 += '''<h3>核心结论</h3>
<ul>
    <li>Agent 互操作与治理进入新阶段：A2A 加入 Agentic AI Foundation、MCP 走向无状态标准化，让企业 Agent 从“孤岛”走向“分层协作”；Binance Agent OS 则把 Agent 带入真实金融操作，隔离与审计成为刚需。</li>
    <li>欧盟 AI 法案透明度条款正式落地：AI 互动披露、合成内容水印、深度伪造标签成为法律义务，企业对外发布 AI 生成内容必须建立合规审查与溯源机制。</li>
    <li>M365 Copilot 进入“计费 + 治理”并行期：Cowork 按量计费、Agent 365 控制平面、Work IQ 统一智能层共同推动 Agentic 办公，但成本管理、数据安全与合规必须先于规模化部署。</li>
    <li>汽车零部件行业 AI 落地主线清晰：物理 AI 重塑智驾（VLA + 世界模型），人形机器人自进化催化汽零供应链，线控底盘、域控制器、热管理成为新增长点；传统制造环节仍应以视觉质检、预测性维护、智能排产为切入点。</li>
    <li>大模型竞争回归“结果与成本”：DeepSeek、智谱、xAI 在低成本与 Agent 能力上发力；OpenAI、Google、Anthropic 在企业级集成、安全、多模态上竞争；英伟达通过世界模型、推理路由与资本平台构建全栈壁垒。</li>
</ul>
<h3>下周观察重点</h3>
<ul>
    <li>微软 Copilot Cowork 首个完整计费月的企业反馈与典型成本案例。</li>
    <li>A2A/MCP 生态首批企业级落地案例与 Agent 商店进展。</li>
    <li>欧盟 AI 法案 Article 50 执法首批案例与罚款动向。</li>
    <li>DeepSeek、智谱 GLM-5.3、xAI Grok 4.6 在汽车/制造行业的落地案例与 API 稳定性。</li>
    <li>8 月汽车销量、智驾渗透率与 Tier 1 线控底盘/域控制器订单落地情况。</li>
    <li>人形机器人产业链（减速器、电机、丝杠、传感器）订单及汽零企业跨界进展。</li>
</ul>
<h3>数据来源与免责声明</h3>
<div class="quote">
    <strong>数据来源：</strong>本简报数据与观点来自 JustSayAI 早晚报（https://www.justsayai.org/）、人民公园说AI 播客/博客、Microsoft 365 Blog / Microsoft Learn、OpenAI 官方、TechCrunch、Axios、aitechconnect.in、钛媒体、新浪财经、东方财富、界面新闻、央视网、知乎、公开行业资讯等渠道。汽车行业案例基于行业公开报道、券商研报与企业实践整理。部分内容基于公开信息的解读与归纳，仅供参考，不构成投资建议。建议读者关注官方渠道获取完整资讯。
</div>'''
sec6 += section_end()

body = f'''<body>
    <nav class="navbar">
        <div class="nav-container">
            <a href="index.html" class="nav-brand">
                <div class="nav-brand-icon">多</div>
                <span>DuoDuo Research</span>
            </a>
            <div class="nav-links">
                <a href="index.html">首页</a>
                <a href="index.html#geopolitical">市场与地缘</a>
                <a href="index.html#ai-tech" class="active">AI 与科技</a>
                <a href="index.html#auto">中国汽车</a>
                <a href="index.html#research">专题研究</a>
            </div>
        </div>
    </nav>
    <div class="breadcrumb">
        <a href="index.html">研究报告中心</a><span>→</span><a href="index.html#ai-tech">AI 与科技</a><span>→</span>AI 智能体与 M365 Copilot 企业资讯简报 | 2026 年 8 月 26 日
    </div>
    <nav class="nav">
        <div class="container nav-content">
            <div class="nav-logo"><div class="nav-logo-icon">AI</div><span>企业 AI 简报</span></div>
            <div class="nav-links">
                <a href="#sec1">AI Agent</a>
                <a href="#sec2">M365 Copilot</a>
                <a href="#sec3">汽车 AI</a>
                <a href="#sec4">大模型</a>
                <a href="#sec5">创作者</a>
                <a href="#sec6">总结</a>
            </div>
        </div>
    </nav>
    <header class="hero">
        <div class="container hero-content">
            <div class="eyebrow">AI Weekly Report · Enterprise Intelligence</div>
            <h1>AI 智能体与 M365 Copilot 企业资讯简报</h1>
            <p class="subtitle">面向汽车零部件行业 CIO / 数字化负责人：追踪 AI Agent、M365 Copilot、行业落地案例与大模型竞争格局。</p>
            <div class="meta">
                <div class="meta-item"><div class="meta-dot"></div><span>2026 年 8 月 26 日</span></div>
                <div class="meta-item"><div class="meta-dot"></div><span>第 7 期</span></div>
                <div class="meta-item"><div class="meta-dot"></div><span>数据来源：JustSayAI、人民公园说AI、微软官方、OpenAI、TechCrunch、公开行业资讯</span></div>
            </div>
        </div>
    </header>
    <main class="container">
        <div class="toc">
            <h2>目录</h2>
            <ul>
                <li><a href="#sec1">一、AI Agent 前沿动态</a></li>
                <li><a href="#sec2">二、M365 Copilot 新闻与案例</a></li>
                <li><a href="#sec3">三、汽车零部件行业 AI 应用</a></li>
                <li><a href="#sec4">四、大模型竞争与产业格局</a></li>
                <li><a href="#sec5">五、中文 AI 创作者/资讯源精选</a></li>
                <li><a href="#sec6">六、总结与下周观察重点</a></li>
            </ul>
        </div>
{sec1}
{sec2}
{sec3}
{sec4}
{sec5}
{sec6}
    </main>
    <footer class="footer">
        <div class="container">
            <p>由企业 AI 资讯系统整理生成 · 2026 年 8 月 26 日</p>
            <p>GitHub 仓库：<a href="https://github.com/hosamzj/sites">github.com/hosamzj/sites</a></p>
        </div>
    </footer>
    <div class="back-to-top" id="backToTop" onclick="window.scrollTo({{top: 0, behavior: 'smooth'}})">↑</div>
    <script>
        const backToTop = document.getElementById('backToTop');
        window.addEventListener('scroll', () => {{
            if (window.scrollY > 500) {{ backToTop.classList.add('visible'); }} else {{ backToTop.classList.remove('visible'); }}
        }});
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {{
            anchor.addEventListener('click', function(e) {{
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {{ target.scrollIntoView({{ behavior: 'smooth', block: 'start' }}); }}
            }});
        }});
    </script>
</body>'''

html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI 智能体与 M365 Copilot 企业资讯简报 | 2026 年 8 月 26 日</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    {css}
</head>
{body}
</html>'''

open(out_path, 'w', encoding='utf-8').write(html)
print('Generated', out_path, 'size', os.path.getsize(out_path))
