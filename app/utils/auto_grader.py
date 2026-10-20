"""
自动评分工具模块
采用"基础分 + 多维度定档加分"方案：
  - 基础分：代码能正确运行即得40分
  - 加分部分（满分60分）由AI在四个维度上定档：
    - 题目符合度：0/6/12/18/24/30 分（6档，权重50%）
    - 正确性：    0/4/8/12/16 分（5档，权重27%）
    - 规范性：    0/2/4/6/10 分（5档，权重17%）
    - 高效性：    0/1/2/3/4 分（5档，权重6%）
"""
import json
import logging
import re
from .llm import call_llm_with_prompt

logger = logging.getLogger(__name__)

BASE_SCORE = 40  # 基础分

# 各维度的可选加分档位（总和60分）
BONUS_TIERS = {
    'requirement': [0, 6, 12, 18, 24, 30],   # 题目符合度，最大贡献30分（50%）
    'correctness': [0, 4, 8, 12, 16],         # 正确性，最大贡献16分（27%）
    'quality':     [0, 2, 4, 6, 10],           # 规范性，最大贡献10分（17%）
    'efficiency':  [0, 1, 2, 3, 4],            # 高效性，最大贡献4分（6%）
}


def auto_grade_submission(assignment_id, code, stdout, stderr, images=None):
    """自动评分函数"""
    from app.models import Assignment

    assignment = Assignment.query.get(assignment_id)
    if not assignment:
        logger.error(f"作业不存在: assignment_id={assignment_id}")
        return None, "作业不存在"

    total_score = assignment.total_score
    description = assignment.description or ""

    if not code or not code.strip():
        return 0, "未提交代码，得0分"

    if stderr and ("Error" in stderr or "Traceback" in stderr):
        return 0, f"代码运行出错，得0分。错误信息：{stderr[:200]}"

    is_plotting_assignment = is_plotting_task(description)

    if not is_plotting_assignment and not stdout and not stderr:
        return 0, "代码无运行结果，得0分"

    try:
        logger.info(f"开始AI评分: assignment_id={assignment_id}, is_plotting={is_plotting_assignment}")
        score, feedback = grade_with_ai(
            assignment_title=assignment.title,
            assignment_description=description,
            student_code=code,
            stdout=stdout,
            stderr=stderr,
            images=images,
            total_score=total_score,
            is_plotting=is_plotting_assignment
        )
        logger.info(f"AI评分完成: assignment_id={assignment_id}, score={score}")
        return score, feedback
    except Exception as e:
        logger.error(f"AI评分失败: {e}")
        return None, "系统繁忙，请等待人工评分"


def is_plotting_task(description):
    """判断是否是画图作业"""
    plotting_keywords = [
        'matplotlib', 'plt', 'plot', '画图', '绘制', '图表',
        '可视化', 'figure', '图像', '图片', 'graph', 'chart',
        '折线图', '柱状图', '饼图', '散点图', '直方图', '热力图'
    ]
    description_lower = description.lower()
    for keyword in plotting_keywords:
        if keyword.lower() in description_lower:
            return True
    return False


def grade_with_ai(assignment_title, assignment_description, student_code, stdout, stderr, images, total_score, is_plotting=False):
    """
    使用 AI 进行定档评分
    AI 只需在每个维度选择一个档位，系统自动计算加分
    """

    scoring_dimensions = """
## 评分规则
代码能正确运行即获得基础分40分。剩余60分由你在以下四个维度中选择档位：

### 1. 题目符合度（选择一档：0/6/12/18/24/30）
这是最重要的维度，决定代码是否满足作业要求。
- 30分：完全满足所有要求
- 24分：满足大部分要求，有1-2处小遗漏
- 18分：满足核心要求，但有多处遗漏
- 12分：只满足部分要求
- 6分：基本未满足要求
- 0分：完全不相关

### 2. 正确性（选择一档：0/4/8/12/16）
- 16分：结果完全正确
- 12分：结果基本正确，有小瑕疵
- 8分：结果有部分错误
- 4分：结果错误较多
- 0分：结果完全错误

### 3. 规范性（选择一档：0/2/4/6/10）
- 10分：结构清晰，命名规范，有适当注释
- 6分：较规范，有少量可改进之处
- 4分：基本可读，但缺少注释或命名不够规范
- 2分：可读性较差，结构混乱
- 0分：完全无规范可言

### 4. 高效性（选择一档：0/1/2/3/4）
- 4分：简洁高效，算法选择合理
- 3分：较简洁，有少量冗余
- 2分：能用但有明显可优化之处
- 1分：有较多冗余或低效写法
- 0分：完全不可用
"""

    plotting_note = ""
    if is_plotting:
        plotting_note = """
## 画图作业特别说明
- 是否调用 plt.show() 或 plt.savefig() 不影响评分
- 是否生成图片文件不影响评分
- 只关注代码逻辑本身是否正确实现了图表功能
"""

    prompt = f"""你是一个友善的编程作业评分老师。请对学生的代码进行定档评分。

## 重要说明
- 学生群体是文科生，不是专业计算机学生，请适当放宽评分标准
- 只要代码能正确运行并基本实现功能，就应该给较高的分数
- 对于代码规范性和高效性，不要过于苛刻，能用即可
- 评语要以鼓励为主，指出优点，温和地提出改进建议

## 作业信息
- 作业标题：{assignment_title}
- 作业要求：{assignment_description}

## 学生代码
```python
{student_code}
```

## 代码运行结果
- 标准输出：{stdout if stdout else '无输出'}
- 错误输出：{stderr if stderr else '无错误'}
- 生成图片数量：{len(images) if images else 0}

{scoring_dimensions}
{plotting_note}

请严格按照以下JSON格式返回（只返回JSON，不要包含markdown代码块标记）：
{{"requirement": 30, "correctness": 16, "quality": 6, "efficiency": 3, "feedback": "评语内容"}}

字段说明（每个字段只能填指定的档位值）：
- requirement: 题目符合度，只能是 0/6/12/18/24/30 中的一个
- correctness: 正确性，只能是 0/4/8/12/16 中的一个
- quality: 规范性，只能是 0/2/4/6/10 中的一个
- efficiency: 高效性，只能是 0/1/2/3/4 中的一个
- feedback: 纯文本评语，100字以内，以鼓励为主，温和指出改进建议
"""

    response = call_llm_with_prompt(prompt, max_tokens=2000)
    return parse_ai_response(response, total_score)


def parse_ai_response(response, total_score):
    """解析AI返回的定档评分结果"""
    if not response:
        return None, "系统繁忙，请等待人工评分"

    cleaned = response.strip()
    json_block_pattern = r'```(?:json)?\s*\n?([\s\S]*?)\n?\s*```'
    match = re.search(json_block_pattern, cleaned)
    if match:
        cleaned = match.group(1).strip()

    try:
        result = json.loads(cleaned)

        # 提取各维度加分（自动匹配最近的档位）
        req_bonus = snap_to_tier(result.get('requirement', 0), BONUS_TIERS['requirement'])
        cor_bonus = snap_to_tier(result.get('correctness', 0), BONUS_TIERS['correctness'])
        qua_bonus = snap_to_tier(result.get('quality', 0), BONUS_TIERS['quality'])
        eff_bonus = snap_to_tier(result.get('efficiency', 0), BONUS_TIERS['efficiency'])
        feedback = result.get('feedback', '评分完成')

        # 最终分数 = 基础分 + 各维度加分之和
        final_score = BASE_SCORE + req_bonus + cor_bonus + qua_bonus + eff_bonus

        # 映射到固定档位：>=90→100, >=80→80, >=70→70, >=60→60
        final_score = snap_score_to_tier(final_score)

        # 映射到作业满分
        final_score = round(final_score * total_score / 100)

        return final_score, feedback

    except (json.JSONDecodeError, ValueError, TypeError) as e:
        logger.warning(f"JSON解析失败: {e}")

    score = extract_score_from_text(response, total_score)
    if score is not None:
        return score, "AI评分完成"

    logger.error(f"无法解析AI评分结果: {response[:200]}")
    return None, "系统繁忙，请等待人工评分"


def snap_to_tier(value, tiers):
    """将AI返回的值匹配到最近的档位"""
    try:
        value = int(value)
    except (ValueError, TypeError):
        return tiers[0]

    if value in tiers:
        return value

    return min(tiers, key=lambda t: abs(t - value))


def snap_score_to_tier(score):
    """将最终分数映射到固定档位：100/80/70/60/0"""
    if score >= 90:
        return 100
    elif score >= 80:
        return 80
    elif score >= 70:
        return 70
    elif score >= 60:
        return 60
    else:
        return score  # 60以下保持原值（0分场景）


def extract_score_from_text(text, total_score):
    """从文本中提取评分分数（兜底方案）"""
    patterns = [
        r'"score"\s*:\s*(\d+)',
        r'得分[：:]\s*(\d+)',
        r'分数[：:]\s*(\d+)',
        r'总[分得][：:]\s*(\d+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                score = int(match.group(1))
                if 0 <= score <= total_score:
                    return score
            except ValueError:
                continue
    return None
