import re, os

base = os.path.expanduser('~/Sites')
tmpl_path = os.path.join(base, 'ai-weekly-report-2026-08-26.html')
out_path = os.path.join(base, 'ai-weekly-report-2026-09-03.html')

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
sec1 = section_start('sec1', '一、AI Agent 前沿动态', '本周 AI Agent 的核心叙事是“能力跃升 + 安全焦虑 + 协议治理”。OpenAI 发布新一代 Astra 模型，具备自主发现并利用未知系统漏洞的能力，引发前沿安全讨论；Anthropic 推出 Fable / Mythos 5.1，强调低成本、低限制与企业级零数据保留。中国市场中，千问接入高德打车等“AI 办事”场景快速铺开，DeepSeek Harness 继续推动 Agent 工厂化。企业级部署必须在能力提升与风险管控之间建立硬边界。')
sec1_cards = [
    card('🛡️', 'OpenAI Astra：能自主发现并利用零日漏洞的前沿模型',
         '9 月 1 日，OpenAI 披露即将发布的 Astra 模型在 ExploitBench 安全评测中获得满分，并在内部修改版测试中自主发现并利用了两处零日漏洞。OpenAI 称这是首个达到其“关键网络安全阈值”的大模型，但表示最先进的安全能力将受限开放。与 Anthropic 此前对 Mythos 模型的担忧类似，Astra 的发布再次凸显前沿模型在网络安全领域的双面性。',
         'TechCrunch 2026-09-01 / OpenAI 官方博客'),
    card('🔓', 'Anthropic 发布 Fable / Mythos 5.1：更便宜、更少限制、零数据保留',
         '9 月 1 日，Anthropic 发布 Fable 5.1 和 Mythos 5.1。Fable 作为无限制版本面向所有 API 和云平台开放，Mythos 5.1 仅向网络安全与生命科学领域的注册合作伙伴开放。新模型在多项基准测试中创纪录，并首次为企业提供“零数据保留”选项，允许客户在自有基础设施上运行模型而不外传数据，同时保留滥用监控能力。',
         'TechCrunch 2026-09-01 / Anthropic 官方公告'),
    card('🚕', '中国 Agent 落地提速：千问接入高德打车，AI 变成“数字管家”',
         'JustSayAI 观察指出，国内 AI Agent 已率先在日常生活服务中落地：用户可通过通义千问直接呼叫高德打车，无需在多个 App 间切换。相比 OpenAI Operator 依赖浏览器自动化、容易卡在验证码，中国 Agent 通过深度集成本地服务 API，实现了“开口即办事”。对汽车零部件企业而言，这种“ deep integration（深度集成）”模式是 Agent 从 Demo 走向生产的关键路径。',
         'JustSayAI 博客 2026-08 / 行业观察'),
    card('🏭', 'DeepSeek Harness：Agent 工厂化与治理复杂度同步上升',
         'DeepSeek Harness 被定位为“造 Agent 的工厂”而非“整车”：它提供模块化、可插拔的底层组件，让开发者像搭建生产线一样拼装 Agent。这降低了 Agent 开发门槛，但也意味着兼容性、版本控制、权限隔离和审计追踪的治理复杂度显著上升。企业 IT 负责人需在“自由组装”与“可控运维”之间找到平衡点。',
         'JustSayAI 博客 2026-08-21'),
    card('⚖️', '欧盟 AI 法案合规持续发酵，企业对外内容须可溯源',
         '欧盟 AI 法案 Article 50 已进入执行期，AI 交互披露、合成内容水印、深度伪造标签成为法律义务。Anthropic 等企业已开始为生成内容嵌入 C2PA 来源元数据与不可见水印。汽车/制造企业若将 Copilot/Claude 生成内容用于客户沟通、营销材料或技术文档，需建立合规审查与溯源机制。',
         'EU AI Act / Anthropic 官方 2026-08'),
    card('🔗', 'MCP/A2A 共治框架持续推进，互操作性从“战争”走向“分层标准”',
         'Google A2A 与 Anthropic MCP 在 Linux Foundation Agentic AI Foundation 下共存，前者解决 Agent 之间的水平协作，后者解决 Agent 与工具/数据的垂直集成。本周多家云服务商与 SaaS 平台继续推出 MCP/A2A 兼容接口，企业 Agent 互操作性逐步从概念走向可落地的分层标准。',
         'aitechconnect.in / Axios / 公开报道 2026-08/09'),
]
sec1 += cards_grid(sec1_cards) + highlight('<strong>高管视角：</strong>本周 Agent 能力边界显著外推：Astra 能自主发现漏洞，Fable 降低企业使用门槛，中国 Agent 在生活服务中率先跑通。但能力越强，越需要“身份最小化、操作审计、沙箱隔离、预算上限、人工复核”作为前置条件。汽车/制造企业应将 Agent 治理纳入 IT 风险管理体系，而非仅作为效率工具试点。') + section_end()

sec2 = section_start('sec2', '二、M365 Copilot 新闻、功能更新与企业案例', '本周 M365 Copilot 的核心动向是“多模型升级 + Agentic 能力 GA + 制造业场景渗透”。Anthropic Claude Opus 5 正式加入 M365 Copilot 模型阵容；Word、Excel、PowerPoint 的 Agentic 功能全面可用；Work IQ API 进入公测，为 Agent-to-Agent 通信提供统一智能层；Dynamics 365 面向制造业推出新的 Agentic 能力。Copilot 正从“个人助理”进化为“企业智能操作系统”。')
sec2_cards = [
    card('🧠', 'Anthropic Claude Opus 5 正式入驻 Microsoft 365 Copilot',
         '微软 Microsoft 365 Roadmap 显示，Anthropic Claude Opus 5 已可在 M365 Copilot 中使用。这是继 GPT-5.5 Thinking 之后，Copilot 多模型战略的又一关键落子。企业用户可在推理强度、代码能力、长文本处理等场景中选择更合适的底层模型，同时需建立模型版本管理与安全评估流程。',
         'Microsoft 365 Roadmap 2026-08'),
    card('📊', 'Copilot Agentic 功能在 Word、Excel、PowerPoint 全面可用',
         '微软宣布 Copilot 在 Word、Excel、PowerPoint 中的 Agentic 能力正式 GA。用户可让 Copilot 跨文档执行多步骤任务，例如根据邮件和会议纪要从零生成报告、自动更新数据透视表、基于品牌规范调整演示文稿。对汽车零部件企业，这意味着技术文档、质量报告与汇报材料的生成效率可进一步提升。',
         'Microsoft 365 Blog / Microsoft Learn 2026-08'),
    card('🔌', 'Work IQ API 公测：让 Copilot 智能进入 Agent-to-Agent 通信',
         'Work IQ API 进入公开预览，允许企业将 Microsoft 365 中的工作关系、会议、邮件、文件上下文开放给自定义 Agent 使用。这标志着 Copilot 的智能层开始从“人机交互”延伸到“机机协作”，是构建企业级多 Agent 系统的关键基础设施。',
         'Microsoft 365 Roadmap 2026-08'),
    card('🏭', 'Dynamics 365 推出面向制造业的 Agentic 能力',
         '微软 Dynamics 365 新增覆盖制造业的 Agentic 功能，包括生产排程优化、供应链异常预警、设备维护建议等。这些能力可直接与 M365 Copilot 和 Microsoft Agent 365 控制平面联动，帮助汽车零部件企业打通办公智能与运营智能。',
         'Microsoft 365 Roadmap / Dynamics 365 Blog 2026-08'),
    card('🔍', 'Federated Copilot 连接器：把实时企业数据带入 Copilot',
         '微软推出 Federated Copilot connectors，允许企业将实时业务数据（如 ERP、MES、CRM）安全接入 Copilot 上下文。对制造企业而言，这意味着 Copilot 可以基于生产、库存、质量等实时数据回答问题，而不局限于 M365 内部数据。',
         'Microsoft 365 Roadmap 2026-08'),
    card('🤝', 'Microsoft Scout：企业级 Agent 探索与安全评估工具',
         '微软在 Roadmap 中公布 Microsoft Scout，定位为帮助企业发现、评估和管理 Agent 的工具。它可识别组织内正在使用的 Agent、评估其权限与数据访问范围，并提供治理建议。这与 Agent 365 控制平面共同构成 Copilot 生态的治理闭环。',
         'Microsoft 365 Roadmap 2026-08'),
]
sec2 += cards_grid(sec2_cards) + model_box([
    ('Cowork 计费要点', '需 M365 Copilot 订阅（$30/用户/月）作为前提；Cowork 用量单独按 Credit 计费，租户级共享额度；可用 P3 预购或 PAYG。'),
    ('汽车行业高价值场景', 'APQP/PPAP 文档协同、全球供应商技术邮件、多语言会议纪要、售后索赔分析、质量报告自动生成、生产排程异常处理。'),
    ('治理优先级', '在开启 Agentic 功能前完成：计费策略、消费预算、敏感度标签、DLP、Entra 访问组、审计日志、人工审批节点。')
]) + section_end()

sec3 = section_start('sec3', '三、汽车零部件行业 AI 应用落地', '本周汽车行业 AI 的核心叙事是“Robotaxi 竞争白热化 + 中国智驾进入物理 AI 阶段 + 制造业 Agent 渗透”。Waymo 在美国扩展至 14 城、车队超 4000 辆，与特斯拉 Cybercab 形成正面交锋；中国市场上 VLA + 世界模型成为智驾主流路线，人形机器人与汽零供应链联动加深。对传统零部件制造，视觉质检、预测性维护、智能排产仍是高 ROI 抓手，而 Copilot 在办公与生产运营中的结合正成为新趋势。')
sec3_cards = [
    card('🚕', 'Waymo 扩张至 14 城，Robotaxi 竞赛进入新阶段',
         '9 月 1 日，Waymo 宣布在丹佛、圣地亚哥和坦帕向公众开放 Robotaxi 服务，商业运营城市增至 14 个，车队规模超过 4000 辆（包括捷豹 I-Pace 和新车型 Ojai）。Waymo 同时发布技术博客，强调“纯端到端”系统不够安全，多传感器融合是实现大规模全无人驾驶的必要路径，被广泛解读为对特斯拉 Cybercab 路线的批评。',
         'TechCrunch 2026-09-01'),
    card('🚗', '特斯拉 Cybercab 即将亮相，Robotaxi 商业模式受关注',
         '特斯拉计划于 9 月 3 日正式发布双座 Cybercab，并将其纳入自有 Robotaxi 车队。目前特斯拉已在奥斯汀、达拉斯、休斯顿、迈阿密、奥兰多和坦帕提供付费无人驾驶 Model Y 服务。Cybercab 无方向盘、无踏板的定制设计，被视为特斯拉规模化 Robotaxi 业务的关键棋子。',
         'TechCrunch 2026-09-01 / 公开报道'),
    card('🧠', '物理 AI 重塑智驾：VLA + 世界模型成为中国主流路线',
         '2026 年以来，小鹏、华为、蔚来、地平线、Momenta 等持续推动 VLA（视觉-语言-动作）与世界模型融合。小米澎湃 N70/N90 将于 9 月 7 日上市，智能驾驶成为核心卖点。黑芝麻智能等行业人士认为，VLA + 世界模型是智驾未来最可能的技术路线，将带动域控制器、传感器、线控底盘等汽零需求。',
         '汽车之家 / 公开行业资讯 2026-08/09'),
    card('🤖', '人形机器人自进化提速，汽零供应链受益',
         '宇树科技等厂商推动物理 AI 机器人模型自进化：利用大模型在设定规则、经验与约束下，自主检索论文、生成控制代码并在仿真/实物上部署测试。中国在人形机器人供应链完整度、成本控制和快速量产上优势明显；汽零企业的精密加工与量产能力是机器人成本下探的核心支撑。',
         '东方财富 / 界面新闻 2026-08'),
    card('⚙️', '线控底盘与域控制器：从机械件到智能执行器',
         '浙江世宝定增近 14 亿元投向线控转向；卓驭科技展示全栈移动物理 AI 智驾方案。物理 AI 正把汽车零部件从“机械件”升级为“智能执行器”，线控底盘、智能悬架、热管理系统与边缘计算平台迎来新一轮订单周期。',
         '公开行业资讯 2026-08'),
    card('💼', 'M365 Copilot 与 Dynamics 365 联动：制造运营智能升级',
         '微软 Dynamics 365 面向制造业的 Agentic 能力，可与 M365 Copilot 和 Agent 365 控制平面联动。汽车零部件企业有望通过自然语言交互，查询生产进度、识别供应链异常、触发维护工单，实现从办公到运营的智能协同。',
         'Microsoft 365 Roadmap / 行业观察'),
]
sec3 += cards_grid(sec3_cards)
sec3 += '<h3>高 ROI 落地场景优先级</h3>'
sec3 += table([
    ['优先级', '场景', '适用技术', '预期收益'],
    ['<span class="status status-success"><span class="status-dot"></span>高</span>', '视觉质检', '计算机视觉 + 缺陷检测', '漏检率降 40–60%，年省数十万至数百万'],
    ['<span class="status status-success"><span class="status-dot"></span>高</span>', '预测性维护', '时序预测 + 传感器数据', '非计划停机降 20–30%，维护成本降 15–25%'],
    ['<span class="status status-success"><span class="status-dot"></span>高</span>', '智能排产', '运筹优化 + 强化学习', '产能利用率提升 15–20%，交付周期缩短 10–15%'],
    ['<span class="status status-accent"><span class="status-dot"></span>中</span>', '办公效率提升', 'M365 Copilot + 知识库', '文档/会议/数据分析效率提升 30–50%'],
    ['<span class="status status-accent"><span class="status-dot"></span>中</span>', '生产运营智能', 'Dynamics 365 Agentic + Copilot', '异常响应提速，跨部门协同效率提升'],
    ['<span class="status status-warning"><span class="status-dot"></span>待观察</span>', '生成式 AI 研发设计', 'CAD/CAE 集成、生成式设计', '长期潜力大，短期需验证数据与合规'],
])
sec3 += highlight('<strong>落地路径建议：</strong>第一阶段（1–3 个月）选择 1–2 个高 ROI 制造场景试点；第二阶段（3–6 个月）扩展至多产线并建立 MLOps，同步引入 M365 Copilot 办公效率场景；第三阶段（6–12 个月）打通 Dynamics 365 生产运营数据，构建“办公智能 + 运营智能”双轮驱动；长期建立 AI 治理体系（安全、合规、数据隐私、模型可审计）。') + section_end()

sec4 = section_start('sec4', '四、大模型竞争与产业格局', '本周大模型竞争呈现“安全能力军备竞赛 + 企业级隐私升级 + 多模型生态分化”的格局。OpenAI Astra 与 Anthropic Mythos 5.1 在前沿安全与网络安全领域正面交锋；Anthropic 零数据保留策略向企业客户释放信任信号；Copilot 同时集成 GPT-5.5 Thinking 与 Claude Opus 5，多模型路由成为企业级标配。')
sec4_cards = [
    card('🛡️', 'OpenAI Astra：前沿模型的网络安全双面性',
         'OpenAI 即将推出的 Astra 模型具备自主发现并利用未知系统漏洞的能力，在 ExploitBench 中获得满分。公司表示将采取更严格的访问控制，并会与测试人员合作评估风险。这再次引发关于前沿模型安全治理与开源/开放程度的行业辩论。',
         'TechCrunch / OpenAI 2026-09-01'),
    card('🔐', 'Anthropic 零数据保留：企业级信任竞争升级',
         'Anthropic 在 Fable / Mythos 5.1 发布中宣布“零数据保留”企业选项，允许客户在自有基础设施上运行模型，避免数据外流。这在企业级市场是一个重要差异化信号：当模型能力趋于接近时，数据隐私、合规与可审计性将成为选型关键。',
         'TechCrunch / Anthropic 2026-09-01'),
    card('🏥', 'ChatGPT Health 接入 Epic EHR：医疗 Agent 进入临床工作流',
         'OpenAI 宣布 ChatGPT Health 与 Epic 电子健康记录系统集成，覆盖超过 3.25 亿患者数据。医生可在 EHR 工作流中导入预约记录、实验室结果、用药与专科文档，并由 AI 生成摘要与就诊准备。该集成为只读访问，AI 不会写回数据。',
         'TechCrunch 2026-09-01'),
    card('🛒', '亚马逊 Alexa“Update Me When”：购物 Agent 的主动推送',
         '亚马逊为 Alexa for Shopping 推出“Update Me When”功能，可在用户喜爱的品牌发布新品、节目更新、演唱会公布或新书上市时主动提醒。这标志着消费级 AI Agent 从“被动应答”向“主动预测需求”演进。',
         'TechCrunch 2026-09-01'),
    card('🔧', 'Empirik 融资 2100 万美元：用 AI 预测基础设施故障',
         '红杉孵化的 Empirik 宣布完成 2100 万美元种子轮融资，产品通过追踪系统变更并推断其潜在连锁反应，在故障发生前预测 outages。这对制造业 IT/OT 基础设施的稳定性管理具有参考价值。',
         'TechCrunch 2026-09-01'),
    card('🇨🇳', '中国大模型调用量全球领先，ToB 落地加速',
         '央视网等报道，中国 AI 大模型调用量持续保持全球前列，多个国产模型接连迭代。JustSayAI 观察指出，中国 AI 已将重点从“C 端聊天”转向“任务执行”与“制造业结果交付”，Token 成本与场景深度成为竞争核心。',
         '央视网 / JustSayAI 2026-08/09'),
]
sec4 += cards_grid(sec4_cards) + quote('大模型竞争正从“参数规模 + 榜单分数”转向“安全可控 + 企业级隐私 + 场景结果 + 生态锁定”。国产模型在 ToB 落地、Token 成本、开源可控上优势明显；海外闭源模型在企业级安全、合规、多模态工具链上领先。企业选型应回归业务结果，避免为“排队资格”支付溢价。') + section_end()

sec5 = section_start('sec5', '五、中文 AI 创作者/资讯源精选', '本章整合 JustSayAI 近期博客核心观点，作为中文独立视角呈现。')
sec5_cards = [
    card('🏢', 'AI 办公：大厂抢的不是效率工具，而是“打工数据”',
         'JustSayAI 认为，AI 办公赛道表面上是效率之争，实则是云厂商争夺高质量工作数据与 Token 消耗入口。只要 AI 进入工作群聊，上下文读取就会带来指数级 Token 消耗，云业务成为最大受益者。',
         'JustSayAI 博客《AI办公这个垃圾赛道，大厂到底在抢什么？》'),
    card('🚕', '中国 Agent 落地：硅谷还在梦游，中国已经收割',
         '相比 OpenAI Operator 依赖浏览器自动化，中国 Agent 通过深度集成本地服务 API（如千问 + 高德打车），实现了“开口即办事”。真正的 AI 不是宏大叙事，而是让普通用户无需学习就能把事情办成。',
         'JustSayAI 博客《当 AI 开始替你办事》'),
    card('🏭', '中国把 AI 干成了制造业：Token 顺差时代来临',
         'JustSayAI 指出，中国模型已将 Token 成本压至极低水平，让企业能以“雇佣数字实习生”的成本部署 AI Agent。未来谁掌握最廉价、最高效的 Token 资产，谁就掌握 AI 帝国的咽喉。',
         'JustSayAI 博客《全球首份大模型财报！中国硬生生把AI干成了制造业！》'),
    card('🏗️', 'DeepSeek Harness：99% 的人不配用它',
         'DeepSeek Harness 被比喻为“造车工厂的生产线”，提供极度自由的模块化组装能力。但自由越大，维修责任越大，兼容性与治理成为企业使用前的必修课。',
         'JustSayAI 博客《99%的人不配用它！｜DeepSeek Harness是一座造Agent的工厂啊！》'),
    card('🚗', '智驾终局是物理 AI，L4 可能比 L3 更快',
         '人民公园说AI 对话千里智驾 CTO 杨沐指出，端到端 + BEV 已触及瓶颈，L3 人机共驾责任边界难以清晰；L4 通过限定场景与系统冗余可能更快实现商业化。',
         'JustSayAI 博客《智驾的终局是物理AI，L4可能比L3更快？》'),
]
sec5 += cards_grid(sec5_cards)
sec5 += '<div class="source">订阅渠道：JustSayAI 博客 https://www.justsayai.org/blog | 人民公园说AI 播客/YouTube/B 站</div>' + section_end()

sec6 = section_start('sec6', '六、总结与下周观察重点', '')
sec6 += '''<h3>核心结论</h3>
<ul>
    <li>Agent 能力与安全同步升级：OpenAI Astra 展示前沿模型的网络安全能力，Anthropic Fable / Mythos 5.1 强调低成本与企业级隐私。能力越强，越需要把“权限最小化、沙箱隔离、审计追踪、人工复核”作为前置条件。</li>
    <li>中国 Agent 落地路径清晰：通过深度集成本地服务 API，千问等 Agent 已在生活场景中实现“开口即办事”。汽车零部件企业可借鉴此思路，将 Agent 与 ERP/MES/CRM 深度连接，而非停留在聊天框层面。</li>
    <li>M365 Copilot 进入“多模型 + Agentic + 运营智能”阶段：Claude Opus 5、GPT-5.5 Thinking 共同提供服务；Word/Excel/PowerPoint Agentic 功能 GA；Work IQ API 与 Dynamics 365 制造业 Agentic 能力推动 Copilot 从办公延伸到生产运营。</li>
    <li>Robotaxi 竞争白热化：Waymo 扩展至 14 城、车队超 4000 辆；特斯拉 Cybercab 即将发布。多传感器融合与纯端到端路线的争论，将深刻影响激光雷达、域控制器、线控底盘等汽零需求。</li>
    <li>汽车零部件行业 AI 主线清晰：物理 AI 重塑智驾（VLA + 世界模型），人形机器人催化汽零供应链，线控底盘/域控制器/热管理成为新增长点；传统制造环节仍应以视觉质检、预测性维护、智能排产为切入点。</li>
</ul>
<h3>下周观察重点</h3>
<ul>
    <li>特斯拉 Cybercab 9 月 3 日发布后的技术细节、定价与商业模式。</li>
    <li>Waymo 与特斯拉在 Robotaxi 市场的下一步扩张与监管动态。</li>
    <li>OpenAI Astra 的测试者反馈与最前沿安全能力开放范围。</li>
    <li>Anthropic Fable / Mythos 5.1 在企业客户中的接受度与零数据保留落地情况。</li>
    <li>M365 Copilot Agentic 功能 GA 后的企业反馈与典型使用成本。</li>
    <li>小米澎湃 N70/N90 9 月 7 日上市对智驾竞争格局的影响。</li>
    <li>8 月汽车销量、新能源渗透率与 Tier 1 线控底盘/域控制器订单落地情况。</li>
</ul>
<h3>数据来源与免责声明</h3>
<div class="quote">
    <strong>数据来源：</strong>本简报数据与观点来自 TechCrunch、Microsoft 365 Roadmap / Microsoft 365 Blog / Microsoft Learn、OpenAI 官方、Anthropic 官方、JustSayAI 博客（https://www.justsayai.org/blog）、人民公园说AI 播客/博客、汽车之家、东方财富、界面新闻、央视网、公开行业资讯等渠道。汽车行业案例基于行业公开报道、券商研报与企业实践整理。部分内容基于公开信息的解读与归纳，仅供参考，不构成投资建议。建议读者关注官方渠道获取完整资讯。
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
        <a href="index.html">研究报告中心</a><span>→</span><a href="index.html#ai-tech">AI 与科技</a><span>→</span>AI 智能体与 M365 Copilot 企业资讯简报 | 2026 年 9 月 3 日
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
                <div class="meta-item"><div class="meta-dot"></div><span>2026 年 9 月 3 日</span></div>
                <div class="meta-item"><div class="meta-dot"></div><span>第 8 期</span></div>
                <div class="meta-item"><div class="meta-dot"></div><span>数据来源：TechCrunch、Microsoft 365 Roadmap、OpenAI、Anthropic、JustSayAI、公开行业资讯</span></div>
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
            <p>由企业 AI 资讯系统整理生成 · 2026 年 9 月 3 日</p>
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
    <title>AI 智能体与 M365 Copilot 企业资讯简报 | 2026 年 9 月 3 日</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    {css}
</head>
{body}
</html>'''

open(out_path, 'w', encoding='utf-8').write(html)
print('Generated', out_path, 'size', os.path.getsize(out_path))
