# -*- coding: utf-8 -*-
"""
专家打分系统 - 完整的数据存储与一致性验证
支持多位专家数据持久化存储、一致性验证和权重计算
一键运行：streamlit run D:\Project\test1.1.py
"""

import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import json
import os
import hashlib
from typing import List, Dict, Tuple, Any
import itertools
from datetime import datetime
import matplotlib

matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Heiti SC', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False
# 设置页面
st.set_page_config(
    page_title="专家打分系统 - AHP权重计算",
    page_icon="👨‍🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 应用标题
st.title("👨‍🎓 专家打分系统 - AHP一致性验证与权重计算")
st.markdown("""
### 大学生人工智能数据素养评价体系专家权重确定
支持多名专家独立打分，数据持久化存储，自动进行一致性验证和权重计算
""")


class ExpertDataManager:
    """专家数据管理器 - 负责数据的持久化存储"""

    def __init__(self, data_file="expert_data.json"):
        self.data_file = data_file
        self.ensure_data_file()

    def ensure_data_file(self):
        """确保数据文件存在"""
        if not os.path.exists(self.data_file):
            # 创建空的专家数据结构
            initial_data = {
                "experts": {},
                "projects": {},
                "analysis_sessions": {},
                "metadata": {
                    "created_time": datetime.now().isoformat(),
                    "last_modified": datetime.now().isoformat(),
                    "version": "1.0"
                }
            }
            self.save_data(initial_data)

    def load_data(self):
        """加载专家数据"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # 如果文件损坏或不存在，重新初始化
            self.ensure_data_file()
            return self.load_data()

    def save_data(self, data):
        """保存专家数据"""
        try:
            # 更新元数据
            data["metadata"]["last_modified"] = datetime.now().isoformat()
            data["metadata"]["total_experts"] = len(data["experts"])

            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            st.error(f"保存数据失败: {e}")
            return False

    def generate_expert_id(self, expert_info):
        """生成专家唯一ID"""
        identifier = f"{expert_info['id']}_{expert_info['name']}_{expert_info['institution']}"
        return hashlib.md5(identifier.encode()).hexdigest()[:12]

    def register_expert(self, expert_info):
        """注册专家"""
        data = self.load_data()
        expert_id = self.generate_expert_id(expert_info)

        if expert_id in data["experts"]:
            return False, "该专家已注册"

        # 添加注册时间
        expert_info["registration_time"] = datetime.now().isoformat()
        expert_info["expert_id"] = expert_id
        expert_info["judgment_matrices"] = {}
        expert_info["consistency_checks"] = {}
        expert_info["active"] = True

        data["experts"][expert_id] = expert_info

        if self.save_data(data):
            return True, expert_id
        else:
            return False, "注册失败"

    def update_expert_judgment(self, expert_id, level, judgment_matrix, weights, cr):
        """更新专家判断数据"""
        data = self.load_data()

        if expert_id not in data["experts"]:
            return False

        # 保存判断矩阵和一致性结果
        data["experts"][expert_id]["judgment_matrices"][level] = {
            "matrix": judgment_matrix.tolist() if hasattr(judgment_matrix, 'tolist') else judgment_matrix,
            "saved_time": datetime.now().isoformat()
        }

        data["experts"][expert_id]["consistency_checks"][level] = {
            "weights": weights.tolist() if hasattr(weights, 'tolist') else weights,
            "consistency_ratio": cr,
            "check_time": datetime.now().isoformat(),
            "status": "excellent" if cr < 0.1 else "acceptable" if cr < 0.2 else "unacceptable"
        }

        return self.save_data(data)

    def get_all_experts(self):
        """获取所有专家"""
        data = self.load_data()
        return data["experts"]

    def get_expert_judgments(self, level):
        """获取指定层次的所有专家判断数据"""
        data = self.load_data()
        judgments = {}

        for expert_id, expert_data in data["experts"].items():
            if level in expert_data["judgment_matrices"] and level in expert_data["consistency_checks"]:
                judgments[expert_id] = {
                    "expert_info": {k: v for k, v in expert_data.items() if
                                    k not in ["judgment_matrices", "consistency_checks"]},
                    "matrix": np.array(expert_data["judgment_matrices"][level]["matrix"]),
                    "weights": np.array(expert_data["consistency_checks"][level]["weights"]),
                    "cr": expert_data["consistency_checks"][level]["consistency_ratio"],
                    "status": expert_data["consistency_checks"][level]["status"]
                }

        return judgments

    def create_analysis_session(self, session_name, description, levels_analyzed):
        """创建分析会话"""
        data = self.load_data()

        session_id = hashlib.md5(f"{session_name}_{datetime.now().isoformat()}".encode()).hexdigest()[:8]

        data["analysis_sessions"][session_id] = {
            "session_name": session_name,
            "description": description,
            "levels_analyzed": levels_analyzed,
            "created_time": datetime.now().isoformat(),
            "expert_count": len(data["experts"]),
            "results": {}
        }

        if self.save_data(data):
            return session_id
        return None

    def save_analysis_results(self, session_id, level, group_weights, analysis_details):
        """保存分析结果"""
        data = self.load_data()

        if session_id in data["analysis_sessions"]:
            data["analysis_sessions"][session_id]["results"][level] = {
                "group_weights": group_weights.tolist() if hasattr(group_weights, 'tolist') else group_weights,
                "analysis_details": analysis_details,
                "analysis_time": datetime.now().isoformat()
            }
            return self.save_data(data)
        return False

    def get_data_statistics(self):
        """获取数据统计"""
        data = self.load_data()
        stats = {
            "total_experts": len(data["experts"]),
            "active_experts": len([e for e in data["experts"].values() if e.get("active", True)]),
            "analysis_sessions": len(data["analysis_sessions"]),
            "last_modified": data["metadata"]["last_modified"]
        }

        # 计算各层次的分析完成情况
        levels = ["一级指标"] + list(ExpertDataManager.get_evaluation_system()["二级指标"].keys())
        level_stats = {}

        for level in levels:
            judgments = self.get_expert_judgments(level)
            level_stats[level] = {
                "completed_experts": len(judgments),
                "acceptable_judgments": len([j for j in judgments.values() if j["cr"] < 0.2])
            }

        stats["level_completion"] = level_stats
        return stats

    @staticmethod
    def get_evaluation_system():
        """获取评价体系结构"""
        return {
            "一级指标": [
                "B1: 系统性认知",
                "B2: 构建式能力",
                "B3: 创造与思辨",
                "B4: 人本与责任"
            ],
            "二级指标": {
                "B1: 系统性认知": [
                    "C11: 数据与知识",
                    "C12: 算法与模型",
                    "C13: 算力与系统",
                    "C14: 交叉与应用",
                    "C15: 可信与安全"
                ],
                "B2: 构建式能力": [
                    "C21: 问题抽象与定义",
                    "C22: 分解与模块化",
                    "C23: 工具选择与模型构建",
                    "C24: 验证、评估与迭代",
                    "C25: 结果解释与沟通"
                ],
                "B3: 创造与思辨": [
                    "C31: 跨情境迁移与应用",
                    "C32: 事实核查与逻辑批判",
                    "C33: 自主规划与个性化学习",
                    "C34: 主动探索与创造",
                    "C35: 学习过程反思与元认知"
                ],
                "B4: 人本与责任": [
                    "C41: 数据安全与隐私保护",
                    "C42: 算法偏差与模型幻觉",
                    "C43: AI向善和以人为本",
                    "C44: 人机协同的责任界定",
                    "C45: 知识普惠与社会公平"
                ]
            }
        }


class AHPExpertScoringSystem:
    """AHP专家打分系统"""

    def show_historical_data_viewer(self):
        """显示历史数据查看器"""
        st.sidebar.header("📋 历史数据查看")

        if not st.session_state.current_expert_id:
            st.sidebar.info("请先注册或选择专家")
            return

        expert_data = self.data_manager.load_data()
        expert_info = expert_data["experts"].get(st.session_state.current_expert_id, {})

        if not expert_info.get("judgment_matrices"):
            st.sidebar.info("暂无历史打分数据")
            return

        # 显示有数据的层次
        levels_with_data = list(expert_info["judgment_matrices"].keys())
        selected_level = st.sidebar.selectbox(
            "选择查看层次",
            levels_with_data
        )

        if selected_level and st.sidebar.button("查看详细数据"):
            # 在主界面显示详细历史数据
            st.header(f"📋 {selected_level} - 历史打分详情")

            # 获取历史数据
            historical_data = expert_info["judgment_matrices"][selected_level]
            consistency_data = expert_info["consistency_checks"][selected_level]

            # 显示基本信息
            col1, col2, col3 = st.columns(3)
            col1.metric("保存时间", historical_data["saved_time"][:19])
            col2.metric("一致性比率", f"{consistency_data['consistency_ratio']:.4f}")
            col3.metric("状态", consistency_data["status"])

            # 显示判断矩阵
            st.subheader("🔍 历史判断矩阵")
            criteria = self.evaluation_system[selected_level] if selected_level == "一级指标" else \
            self.evaluation_system["二级指标"][selected_level]

            matrix = np.array(historical_data["matrix"])
            display_df = pd.DataFrame(
                matrix,
                index=criteria,
                columns=criteria
            )

            # 格式化显示
            def format_value(x):
                if x == 1:
                    return "1.00"
                elif x > 1:
                    return f"{x:.2f}"
                else:
                    return f"1/{int(1 / x)}.{str(int(1 / x) % 100):02d}" if 1 / x < 1 else f"{1 / x:.2f}"

            formatted_df = display_df.copy()
            for col in formatted_df.columns:
                formatted_df[col] = formatted_df[col].apply(format_value)

            st.dataframe(formatted_df, use_container_width=True)

            # 显示权重结果
            st.subheader("📊 历史权重结果")
            weights = np.array(consistency_data["weights"])

            weight_data = []
            for i, criterion in enumerate(criteria):
                weight_data.append({
                    '指标': criterion,
                    '权重': weights[i],
                    '权重百分比': f"{weights[i] * 100:.2f}%"
                })

            weight_df = pd.DataFrame(weight_data)
            weight_df = weight_df.sort_values('权重', ascending=False)
            st.dataframe(weight_df, use_container_width=True)

            # 可视化
            fig, ax = plt.subplots(figsize=(10, 6))
            bars = ax.bar(range(len(weights)), weights, color='lightblue', alpha=0.7)
            ax.set_xlabel('指标')
            ax.set_ylabel('权重')
            ax.set_title(f'{selected_level}历史权重分布')
            ax.set_xticks(range(len(weights)))
            ax.set_xticklabels([c[:15] + "..." if len(c) > 15 else c for c in criteria], rotation=45, ha='right')

            for bar, weight in zip(bars, weights):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width() / 2., height + 0.01,
                        f'{weight:.3f}', ha='center', va='bottom')

            plt.tight_layout()
            st.pyplot(fig)

    def __init__(self):
        # 初始化数据管理器
        self.data_manager = ExpertDataManager()

        # AHP标度含义（包含倒数关系的完整说明）
        self.scale_meanings = {
            1: "同等重要",
            2: "稍微重要",
            3: "明显重要",
            4: "强烈重要",
            5: "极端重要",
            1 / 2: "稍微不重要",
            1 / 3: "明显不重要",
            1 / 4: "强烈不重要",
            1 / 5: "极端不重要"
        }

        # 完整的AHP标度选项（包含倒数）
        self.ahp_scales = [1 / 5, 1 / 4, 1 / 3, 1 / 2, 1, 2, 3, 4, 5]

        # 随机一致性指标RI值
        self.ri_values = {
            1: 0, 2: 0, 3: 0.58, 4: 0.90, 5: 1.12,
            6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49
        }

        # 评价体系
        self.evaluation_system = ExpertDataManager.get_evaluation_system()

    def initialize_session_state(self):
        """初始化会话状态"""
        if 'current_expert_id' not in st.session_state:
            st.session_state.current_expert_id = None
        if 'analysis_completed' not in st.session_state:
            st.session_state.analysis_completed = False
        if 'current_level' not in st.session_state:
            st.session_state.current_level = "一级指标"
        if 'current_session_id' not in st.session_state:
            st.session_state.current_session_id = None

    def create_expert_registration(self):
        """创建专家注册界面"""
        st.sidebar.header("👨‍💼 专家注册")

        with st.sidebar.form("expert_registration"):
            st.subheader("专家信息登记")
            expert_name = st.text_input("专家姓名", placeholder="请输入真实姓名")
            expert_id = st.text_input("专家编号", placeholder="机构或系统分配编号")
            institution = st.text_input("工作单位", placeholder="所在高校或机构")
            title = st.selectbox("职称", ["教授", "副教授", "研究员", "副研究员", "其他"])
            domain = st.selectbox("研究领域", [
                "教育技术", "数据科学", "心理学", "统计学",
                "信息管理", "计算机科学", "其他"
            ])
            experience = st.slider("相关领域经验年限", 1, 40, 10)

            submitted = st.form_submit_button("注册专家身份")

            if submitted:
                if expert_name and expert_id:
                    expert_info = {
                        "name": expert_name,
                        "id": expert_id,
                        "institution": institution,
                        "title": title,
                        "domain": domain,
                        "experience": experience
                    }

                    success, result = self.data_manager.register_expert(expert_info)
                    if success:
                        st.session_state.current_expert_id = result
                        st.sidebar.success(f"欢迎 {expert_name} 专家！注册成功。")
                    else:
                        st.sidebar.error(result)
                else:
                    st.sidebar.error("请填写专家姓名和编号")

    def show_expert_management(self):
        """显示专家管理界面"""
        st.sidebar.header("👥 专家管理")

        experts = self.data_manager.get_all_experts()
        if experts:
            expert_list = list(experts.keys())
            expert_display_names = [f"{exp['name']} ({exp['institution']})" for exp in experts.values()]

            selected_expert = st.sidebar.selectbox(
                "选择专家",
                expert_display_names,
                index=0
            )

            if st.sidebar.button("切换专家"):
                # 找到对应的专家ID
                selected_index = expert_display_names.index(selected_expert)
                st.session_state.current_expert_id = expert_list[selected_index]

            # 显示当前专家信息
            if st.session_state.current_expert_id and st.session_state.current_expert_id in experts:
                expert_info = experts[st.session_state.current_expert_id]
                st.sidebar.markdown(f"""
                **当前专家**: {expert_info['name']}
                **单位**: {expert_info['institution']}
                **领域**: {expert_info['domain']}
                **经验**: {expert_info['experience']}年
                **注册时间**: {expert_info['registration_time'][:10]}
                """)

        # 数据显示
        st.sidebar.header("📊 数据概览")
        stats = self.data_manager.get_data_statistics()
        st.sidebar.metric("注册专家数", stats["total_experts"])
        st.sidebar.metric("活跃专家", stats["active_experts"])
        st.sidebar.metric("分析会话", stats["analysis_sessions"])

        if st.sidebar.button("刷新数据"):
            st.rerun()

        # 添加历史数据查看器
        self.show_historical_data_viewer()

    def format_scale_label(self, scale):
        """格式化标度标签，显示分数形式"""
        if scale < 1:
            return f"1/{int(1 / scale)} - {self.scale_meanings[scale]}"
        else:
            return f"{int(scale)} - {self.scale_meanings[scale]}"

    def create_pairwise_comparison_interface(self, criteria: List[str], level: str):
        """创建两两比较打分界面"""
        st.header(f"📝 {level}两两比较打分")

        # 检查是否有历史数据
        historical_matrix = None
        has_historical_data = False
        if st.session_state.current_expert_id:
            expert_data = self.data_manager.load_data()
            expert_info = expert_data["experts"].get(st.session_state.current_expert_id, {})
            if level in expert_info.get("judgment_matrices", {}):
                historical_matrix = np.array(expert_info["judgment_matrices"][level]["matrix"])
                has_historical_data = True
                st.success(
                    f"📋 已加载您的历史打分数据 (保存时间: {expert_info['judgment_matrices'][level]['saved_time'][:19]})")

        st.info(f"请对以下{len(criteria)}个指标进行两两比较，选择相对重要性")

        # 显示AHP标度说明（包含倒数关系）
        with st.expander("📊 AHP标度说明（包含倒数关系）"):
            st.markdown("""
            ### AHP标度含义（1-5标度法）

            **重要程度标度**:
            - **1**: 两个因素同等重要
            - **2**: 一个因素比另一个稍微重要  
            - **3**: 一个因素比另一个明显重要
            - **4**: 一个因素比另一个强烈重要
            - **5**: 一个因素比另一个极端重要

            **倒数关系**:
            - **1/2**: 稍微不重要（2的倒数）
            - **1/3**: 明显不重要（3的倒数）
            - **1/4**: 强烈不重要（4的倒数） 
            - **1/5**: 极端不重要（5的倒数）
            """)

        # 初始化判断矩阵
        n = len(criteria)
        judgment_matrix = np.eye(n)  # 初始化为单位矩阵

        # 创建比较表格
        st.subheader("两两比较矩阵")
        st.info("请选择左边指标相对于右边指标的重要性程度")

        # 使用列布局创建比较界面
        comparisons = []
        for i in range(n):
            for j in range(i + 1, n):
                comparisons.append((i, j, criteria[i], criteria[j]))

        # 分组显示比较项，避免界面过长
        cols_per_row = 2
        for idx in range(0, len(comparisons), cols_per_row):
            cols = st.columns(cols_per_row)
            for col_idx, col in enumerate(cols):
                if idx + col_idx < len(comparisons):
                    i, j, crit1, crit2 = comparisons[idx + col_idx]

                    with col:
                        # 创建对比卡片
                        st.markdown(f"**{crit1}** 🆚 **{crit2}**")

                        # 设置默认值为历史数据（如果存在）
                        default_value = 1
                        if has_historical_data:
                            historical_value = historical_matrix[i, j]
                            # 找到最接近的滑块选项
                            default_value = min(self.ahp_scales, key=lambda x: abs(x - historical_value))

                        # 使用选择滑块
                        importance = st.select_slider(
                            f"选择 {crit1} 相对于 {crit2} 的重要性",
                            options=self.ahp_scales,
                            value=default_value,  # 使用匹配后的历史数据
                            format_func=self.format_scale_label,
                            key=f"comp_{level}_{i}_{j}_{st.session_state.current_expert_id}"
                        )

                        # 显示选择的含义和对应的倒数关系
                        if importance > 1:
                            st.success(f"**选择**: {crit1} 比 {crit2} {self.scale_meanings[importance]}")
                            st.info(f"**对应**: {crit2} 比 {crit1} {self.scale_meanings[1 / importance]}")
                        elif importance < 1:
                            st.warning(f"**选择**: {crit1} 比 {crit2} {self.scale_meanings[importance]}")
                            st.info(f"**对应**: {crit2} 比 {crit1} {self.scale_meanings[1 / importance]}")
                        else:
                            st.info(f"**选择**: {crit1} 和 {crit2} 同等重要")

                        judgment_matrix[i, j] = importance
                        judgment_matrix[j, i] = 1 / importance  # 自动设置倒数关系

        # 显示完整的判断矩阵预览
        st.subheader("🔍 判断矩阵预览")

        # 创建显示用的数据框
        display_matrix = pd.DataFrame(
            judgment_matrix,
            index=[f"{i + 1}. {crit}" for i, crit in enumerate(criteria)],
            columns=[f"{i + 1}. {crit}" for i, crit in enumerate(criteria)]
        )

        # 格式化显示，使矩阵更易读
        def format_matrix_value(x):
            if x == 1:
                return "1"
            elif x > 1:
                return f"{x:.0f}"
            else:
                return f"1/{int(1 / x)}"

        styled_matrix = display_matrix.copy()
        for col in styled_matrix.columns:
            styled_matrix[col] = styled_matrix[col].apply(format_matrix_value)

        st.dataframe(styled_matrix, use_container_width=True)

        # 如果有历史数据，显示对比选项
        if has_historical_data:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 恢复到历史数据"):
                    # 重新加载历史数据到当前矩阵
                    judgment_matrix = historical_matrix.copy()
                    st.rerun()
            with col2:
                if st.button("🔄 重新加载界面"):
                    st.rerun()

        return judgment_matrix

    def calculate_weights_and_consistency(self, judgment_matrix: np.ndarray) -> Tuple[np.ndarray, float, float]:
        """计算权重和一致性指标"""
        n = judgment_matrix.shape[0]

        # 计算特征向量（几何平均法）
        row_products = np.prod(judgment_matrix, axis=1)
        geometric_means = np.power(row_products, 1 / n)
        weights = geometric_means / np.sum(geometric_means)

        # 计算最大特征值
        weighted_sum = np.dot(judgment_matrix, weights)
        lambda_max = np.sum(weighted_sum / weights) / n

        # 计算一致性指标
        ci = (lambda_max - n) / (n - 1) if n > 1 else 0
        ri = self.ri_values.get(n, 1.45)
        cr = ci / ri if ri > 0 else 0

        return weights, cr, lambda_max

    def check_and_display_consistency(self, judgment_matrix: np.ndarray, level: str):
        """检查并显示一致性结果"""
        weights, cr, lambda_max = self.calculate_weights_and_consistency(judgment_matrix)

        # 显示一致性结果
        st.subheader("✅ 一致性检验结果")

        col1, col2, col3 = st.columns(3)
        col1.metric("一致性比率 (CR)", f"{cr:.4f}")
        col2.metric("最大特征值", f"{lambda_max:.4f}")

        if cr < 0.1:
            col3.metric("检验结果", "通过", delta="优秀")
            st.success("✅ 一致性检验通过！判断矩阵具有满意的一致性。")
        elif cr < 0.2:
            col3.metric("检验结果", "可接受", delta="一般")
            st.warning("⚠️ 一致性可接受，但建议检查判断是否合理。")
        else:
            col3.metric("检验结果", "不通过", delta="需修正", delta_color="inverse")
            st.error("❌ 一致性检验未通过！请重新调整判断矩阵。")

        # 显示权重结果
        st.subheader("📊 权重计算结果")
        criteria = self.evaluation_system[level] if level == "一级指标" else self.evaluation_system["二级指标"][level]

        weight_data = []
        for i, criterion in enumerate(criteria):
            weight_data.append({
                '指标': criterion,
                '权重': weights[i],
                '权重百分比': f"{weights[i] * 100:.2f}%"
            })

        weight_df = pd.DataFrame(weight_data)
        weight_df = weight_df.sort_values('权重', ascending=False)
        st.dataframe(weight_df, use_container_width=True)

        # 可视化权重分布
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

        # 柱状图
        bars = ax1.bar(range(len(weights)), weights, color='lightblue', alpha=0.7)
        ax1.set_xlabel('指标')
        ax1.set_ylabel('权重')
        ax1.set_title(f'{level}权重分布')
        ax1.set_xticks(range(len(weights)))
        ax1.set_xticklabels([c[:10] + "..." if len(c) > 10 else c for c in criteria], rotation=45, ha='right')

        for bar, weight in zip(bars, weights):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width() / 2., height + 0.01,
                     f'{weight:.3f}', ha='center', va='bottom')

        # 饼图
        ax2.pie(weights, labels=criteria, autopct='%1.1f%%', startangle=90)
        ax2.set_title(f'{level}权重比例')

        plt.tight_layout()
        st.pyplot(fig)

        return weights, cr

    def save_expert_judgment(self, level: str, judgment_matrix: np.ndarray, weights: np.ndarray, cr: float):
        """保存专家判断结果"""
        if st.session_state.current_expert_id:
            success = self.data_manager.update_expert_judgment(
                st.session_state.current_expert_id, level, judgment_matrix, weights, cr
            )
            if success:
                st.success("✅ 专家判断数据已保存到数据库")
            else:
                st.error("❌ 保存专家判断数据失败")

    def perform_comprehensive_analysis(self, level: str):
        """执行综合性群组分析"""
        st.header("👥 专家群组综合分析")

        # 获取所有专家的判断数据
        expert_judgments = self.data_manager.get_expert_judgments(level)

        if len(expert_judgments) < 2:
            st.warning(f"需要至少2位专家完成{level}的打分才能进行群组分析")
            st.info(f"当前完成{level}打分的专家数: {len(expert_judgments)}")
            return None

        # 筛选一致性可接受的专家
        valid_judgments = {k: v for k, v in expert_judgments.items() if v["cr"] < 0.2}

        if len(valid_judgments) < 2:
            st.error(f"需要至少2位专家的一致性检验通过才能进行群组分析")
            st.info(f"当前一致性可接受的专家数: {len(valid_judgments)}")
            return None

        st.success(f"✅ 找到{len(valid_judgments)}位专家的有效判断数据进行群组分析")

        # 计算群组权重（几何平均）
        all_weights = np.array([result["weights"] for result in valid_judgments.values()])
        group_weights = np.exp(np.mean(np.log(all_weights), axis=0))
        group_weights = group_weights / np.sum(group_weights)  # 归一化

        # 显示群组分析结果
        st.subheader("📈 群组权重结果")

        criteria = self.evaluation_system[level] if level == "一级指标" else self.evaluation_system["二级指标"][level]

        # 权重表格
        weight_data = []
        for i, criterion in enumerate(criteria):
            individual_weights = [result["weights"][i] for result in valid_judgments.values()]
            std_dev = np.std(individual_weights)

            weight_data.append({
                '指标': criterion,
                '群组权重': group_weights[i],
                '权重百分比': f"{group_weights[i] * 100:.2f}%",
                '标准差': f"{std_dev:.4f}",
                '变异系数': f"{(std_dev / group_weights[i]):.2%}" if group_weights[i] > 0 else "N/A",
                '专家意见范围': f"{min(individual_weights):.3f} - {max(individual_weights):.3f}"
            })

        weight_df = pd.DataFrame(weight_data)
        weight_df = weight_df.sort_values('群组权重', ascending=False)
        st.dataframe(weight_df, use_container_width=True)

        # 专家一致性分析
        st.subheader("📊 专家一致性分析")

        fig, axes = plt.subplots(2, 2, figsize=(16, 12))

        # 1. 权重分布箱线图
        weight_data_for_plot = pd.DataFrame({
            criterion: [result["weights"][i] for result in valid_judgments.values()]
            for i, criterion in enumerate(criteria)
        })

        sns.boxplot(data=weight_data_for_plot, ax=axes[0, 0])
        axes[0, 0].set_title('各指标权重专家分布')
        axes[0, 0].set_ylabel('权重')
        axes[0, 0].tick_params(axis='x', rotation=45)

        # 2. 一致性比率分布
        cr_values = [result["cr"] for result in valid_judgments.values()]
        expert_names = [result["expert_info"]["name"] for result in valid_judgments.values()]

        colors = ['green' if cr < 0.1 else 'orange' for cr in cr_values]
        bars = axes[0, 1].bar(expert_names, cr_values, color=colors, alpha=0.7)
        axes[0, 1].axhline(y=0.1, color='red', linestyle='--', label='优秀标准 (CR<0.1)')
        axes[0, 1].axhline(y=0.2, color='orange', linestyle='--', label='可接受标准 (CR<0.2)')
        axes[0, 1].set_title('专家一致性比率分布')
        axes[0, 1].set_ylabel('一致性比率 (CR)')
        axes[0, 1].legend()
        axes[0, 1].tick_params(axis='x', rotation=45)

        # 添加数值标签
        for bar, cr in zip(bars, cr_values):
            height = bar.get_height()
            axes[0, 1].text(bar.get_x() + bar.get_width() / 2., height + 0.01,
                            f'{cr:.3f}', ha='center', va='bottom')

        # 3. 专家权重热图
        weight_matrix = np.array([result["weights"] for result in valid_judgments.values()])
        im = axes[1, 0].imshow(weight_matrix, cmap='YlOrRd', aspect='auto')
        axes[1, 0].set_title('专家权重热图')
        axes[1, 0].set_xlabel('指标')
        axes[1, 0].set_ylabel('专家')
        axes[1, 0].set_xticks(range(len(criteria)))
        axes[1, 0].set_xticklabels([f"{i + 1}" for i in range(len(criteria))])
        axes[1, 0].set_yticks(range(len(expert_names)))
        axes[1, 0].set_yticklabels([name[:8] + "..." if len(name) > 8 else name for name in expert_names])
        plt.colorbar(im, ax=axes[1, 0])

        # 4. 专家共识度散点图
        avg_weights_per_expert = np.mean(weight_matrix, axis=1)
        axes[1, 1].scatter(avg_weights_per_expert, cr_values, alpha=0.6)
        for i, (name, avg_w, cr_val) in enumerate(zip(expert_names, avg_weights_per_expert, cr_values)):
            axes[1, 1].annotate(name[:6], (avg_w, cr_val), xytext=(5, 5), textcoords='offset points', fontsize=8)
        axes[1, 1].set_xlabel('平均权重')
        axes[1, 1].set_ylabel('一致性比率')
        axes[1, 1].set_title('专家权重与一致性关系')
        axes[1, 1].axhline(y=0.1, color='red', linestyle='--', alpha=0.5)
        axes[1, 1].axhline(y=0.2, color='orange', linestyle='--', alpha=0.5)

        plt.tight_layout()
        st.pyplot(fig)

        # 专家共识度统计分析
        st.subheader("🤝 专家共识度统计分析")

        # 计算专家间权重相关性
        weight_correlations = []
        expert_pairs = []

        for i in range(len(valid_judgments)):
            for j in range(i + 1, len(valid_judgments)):
                corr = np.corrcoef(
                    list(valid_judgments.values())[i]["weights"],
                    list(valid_judgments.values())[j]["weights"]
                )[0, 1]
                weight_correlations.append(corr)
                expert_pairs.append((
                    list(valid_judgments.values())[i]["expert_info"]["name"],
                    list(valid_judgments.values())[j]["expert_info"]["name"]
                ))

        avg_correlation = np.mean(weight_correlations) if weight_correlations else 0

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("参与专家数", len(valid_judgments))
        col2.metric("平均一致性", f"{np.mean(cr_values):.3f}")
        col3.metric("专家共识度", f"{avg_correlation:.3f}")
        col4.metric("权重稳定性", f"{1 - np.mean(weight_df['变异系数'].str.rstrip('%').astype(float) / 100):.3f}")

        # 显示专家对相关性
        if len(expert_pairs) <= 10:  # 避免显示过多对
            st.write("**专家对相关性:**")
            pair_data = []
            for (exp1, exp2), corr in zip(expert_pairs, weight_correlations):
                pair_data.append({
                    '专家对': f"{exp1} - {exp2}",
                    '相关性': f"{corr:.3f}",
                    '共识水平': "高" if corr > 0.8 else "中" if corr > 0.6 else "低"
                })
            st.dataframe(pd.DataFrame(pair_data))

        if avg_correlation > 0.8:
            st.success("✅ 专家共识度很高，权重结果非常可靠")
        elif avg_correlation > 0.6:
            st.warning("⚠️ 专家共识度一般，建议进一步讨论")
        else:
            st.error("❌ 专家共识度较低，建议重新评估或增加专家数量")

        # 返回分析详情
        analysis_details = {
            "expert_count": len(valid_judgments),
            "average_consistency": float(np.mean(cr_values)),
            "consensus_level": float(avg_correlation),
            "weight_stability": float(1 - np.mean(weight_df['变异系数'].str.rstrip('%').astype(float) / 100)),
            "expert_names": [exp["expert_info"]["name"] for exp in valid_judgments.values()]
        }

        return group_weights, analysis_details

    def create_analysis_session(self):
        """创建分析会话"""
        st.sidebar.header("💾 分析会话")

        with st.sidebar.form("analysis_session"):
            session_name = st.text_input("会话名称", "人工智能素养权重分析")
            description = st.text_area("描述", "多位专家对人工智能素养指标权重的综合分析")

            if st.form_submit_button("创建分析会话"):
                session_id = self.data_manager.create_analysis_session(
                    session_name, description, ["一级指标", "二级指标"]
                )
                if session_id:
                    st.session_state.current_session_id = session_id
                    st.sidebar.success(f"分析会话创建成功: {session_id}")
                else:
                    st.sidebar.error("创建分析会话失败")

        if st.session_state.current_session_id:
            st.sidebar.info(f"当前会话: {st.session_state.current_session_id}")

    def export_comprehensive_results(self):
        """导出综合分析结果"""
        st.header("📥 综合分析结果导出")

        if not st.session_state.current_session_id:
            st.warning("请先创建分析会话")
            return

        # 收集各层次的分析结果
        level_weights = {}
        analysis_details = {}

        # 一级指标分析
        level1_result = self.perform_comprehensive_analysis("一级指标")
        if level1_result:
            level_weights["一级指标"], analysis_details["一级指标"] = level1_result

        # 二级指标分析
        for first_level in self.evaluation_system["二级指标"].keys():
            level2_result = self.perform_comprehensive_analysis(first_level)
            if level2_result:
                level_weights[first_level], analysis_details[first_level] = level2_result

        if not level_weights:
            st.error("没有可导出的有效分析结果")
            return

        # 构建完整的权重体系
        st.subheader("🏆 完整的人工智能素养权重体系")

        hierarchy_data = []

        if "一级指标" in level_weights:
            level1_weights = level_weights["一级指标"]
            level1_criteria = self.evaluation_system["一级指标"]

            for i, criterion in enumerate(level1_criteria):
                # 一级指标
                level1_weight = level1_weights[i]
                hierarchy_data.append({
                    '层级': '一级指标',
                    '指标编码': criterion.split(':')[0],
                    '指标名称': criterion.split(':')[1],
                    '绝对权重': level1_weight,
                    '相对权重': '100%',
                    '说明': '核心能力维度'
                })

                # 二级指标
                if criterion in level_weights:
                    level2_weights = level_weights[criterion]
                    level2_criteria = self.evaluation_system["二级指标"][criterion]

                    for j, level2_criterion in enumerate(level2_criteria):
                        absolute_weight = level1_weight * level2_weights[j]
                        hierarchy_data.append({
                            '层级': '二级指标',
                            '指标编码': level2_criterion.split(':')[0],
                            '指标名称': level2_criterion.split(':')[1],
                            '绝对权重': absolute_weight,
                            '相对权重': f"{level2_weights[j] * 100:.1f}%",
                            '说明': f"{criterion}的具体表现"
                        })

        hierarchy_df = pd.DataFrame(hierarchy_data)
        st.dataframe(hierarchy_df, use_container_width=True)

        # 导出数据
        st.subheader("💾 数据导出")

        export_data = {
            "system_name": "大学生人工智能素养评价体系",
            "analysis_time": datetime.now().isoformat(),
            "session_id": st.session_state.current_session_id,
            "expert_count": self.data_manager.get_data_statistics()["total_experts"],
            "level_weights": {},
            "analysis_quality": analysis_details,
            "hierarchy_weights": hierarchy_data
        }

        for level, weights in level_weights.items():
            if level == "一级指标":
                criteria = self.evaluation_system[level]
            else:
                criteria = self.evaluation_system["二级指标"][level]

            export_data["level_weights"][level] = {
                "criteria": criteria,
                "weights": weights.tolist() if hasattr(weights, 'tolist') else weights
            }

        # 显示JSON格式
        with st.expander("查看JSON数据"):
            st.json(export_data)

        # 提供下载按钮
        json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
        st.download_button(
            label="下载完整权重JSON文件",
            data=json_str,
            file_name=f"人工智能素养权重分析_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json"
        )

        # 保存到分析会话
        for level, weights in level_weights.items():
            self.data_manager.save_analysis_results(
                st.session_state.current_session_id,
                level,
                weights,
                analysis_details.get(level, {})
            )

        st.success("✅ 分析结果已保存并导出")


def main():
    """主应用"""
    # 初始化系统
    ahp_system = AHPExpertScoringSystem()
    ahp_system.initialize_session_state()

    # 侧边栏
    st.sidebar.title("🔧 系统控制")

    # 专家注册和管理
    ahp_system.create_expert_registration()
    ahp_system.show_expert_management()
    ahp_system.create_analysis_session()

    # 主内容区
    if not st.session_state.current_expert_id:
        st.info("👈 请在左侧栏注册专家身份开始打分")

        # 显示系统概览
        st.header("📈 系统概览")
        stats = ahp_system.data_manager.get_data_statistics()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("总专家数", stats["total_experts"])
        col2.metric("活跃专家", stats["active_experts"])
        col3.metric("分析会话", stats["analysis_sessions"])
        col4.metric("最后更新", stats["last_modified"][:10])

        # 显示各层次完成情况
        st.subheader("各层次分析完成情况")
        level_stats = stats["level_completion"]

        level_data = []
        for level, stats in level_stats.items():
            level_data.append({
                "分析层次": level,
                "完成专家数": stats["completed_experts"],
                "有效判断数": stats["acceptable_judgments"],
                "完成率": f"{(stats['completed_experts'] / max(1, level_stats['一级指标']['completed_experts'])) * 100:.1f}%"
            })

        st.dataframe(pd.DataFrame(level_data))
        return

    # 分析层次选择
    st.sidebar.header("📊 分析设置")
    analysis_level = st.sidebar.radio(
        "选择分析层次",
        ["专家个人打分", "群组一致性分析", "完整权重体系导出"],
        help="选择需要进行的分析类型"
    )

    # 根据选择显示相应的界面
    if analysis_level == "专家个人打分":
        st.sidebar.header("🔍 打分层次选择")
        scoring_level = st.sidebar.radio(
            "选择打分层次",
            ["一级指标", "二级指标"],
            help="选择要进行打分的指标层次"
        )

        if scoring_level == "一级指标":
            st.session_state.current_level = "一级指标"
            criteria = ahp_system.evaluation_system["一级指标"]

            # 显示一级指标说明
            st.header("🎯 一级指标说明")
            st.markdown("""
            **人工智能素养四大核心维度**:
            - **B1: 系统性认知**: 构成AI素养的完整知识框架，涵盖数据、算法、算力等核心要素。
            - **B2: 构建式能力**: 从问题定义到结果呈现的核心技能集，强调AI解决方案的完整构建流程。
            - **B3: 创造与思辨**: 素养的顶峰，强调学生的自主性、批判性思维和创造性应用AI的能力。
            - **B4: 人本与责任**: 关注数据隐私、算法公平、社会伦理等AI向善的核心责任。
            """)

            # 打分界面（现在会自动加载历史数据）
            judgment_matrix = ahp_system.create_pairwise_comparison_interface(criteria, "一级指标")

            if st.button("提交打分并检验一致性", type="primary"):
                weights, cr = ahp_system.check_and_display_consistency(judgment_matrix, "一级指标")
                ahp_system.save_expert_judgment("一级指标", judgment_matrix, weights, cr)

        else:  # 二级指标
            st.sidebar.header("🔍 二级指标选择")
            selected_first_level = st.sidebar.selectbox(
                "选择一级指标",
                ahp_system.evaluation_system["一级指标"]
            )

            if selected_first_level in ahp_system.evaluation_system["二级指标"]:
                criteria = ahp_system.evaluation_system["二级指标"][selected_first_level]
                st.session_state.current_level = selected_first_level

                st.header(f"🔍 {selected_first_level} - 二级指标说明")
                st.info(f"请对{selected_first_level}下的{len(criteria)}个二级指标进行两两比较")

                # 打分界面（现在会自动加载历史数据）
                judgment_matrix = ahp_system.create_pairwise_comparison_interface(criteria, selected_first_level)

                if st.button("提交打分并检验一致性", type="primary"):
                    weights, cr = ahp_system.check_and_display_consistency(judgment_matrix, selected_first_level)
                    ahp_system.save_expert_judgment(selected_first_level, judgment_matrix, weights, cr)


    elif analysis_level == "群组一致性分析":
        st.sidebar.header("🔍 分析层次选择")
        analysis_level_select = st.sidebar.selectbox(
            "选择分析层次",
            ["一级指标"] + list(ahp_system.evaluation_system["二级指标"].keys())
        )

        st.header(f"👥 {analysis_level_select} - 群组一致性分析")
        ahp_system.perform_comprehensive_analysis(analysis_level_select)

    else:  # 完整权重体系导出
        st.header("🏗️ 完整权重体系导出")
        ahp_system.export_comprehensive_results()

    # 使用说明
    with st.sidebar.expander("💡 系统使用说明"):
        st.markdown("""
        **数据存储特性**:
        - ✅ 专家数据持久化保存
        - ✅ 支持多位专家独立打分
        - ✅ 自动一致性验证
        - ✅ 群组权重计算
        - ✅ 分析会话管理

        **操作流程**:
        1. 专家注册个人信息
        2. 进行个人层次打分
        3. 系统自动检验一致性
        4. 进行群组一致性分析
        5. 导出完整权重体系

        **数据文件**: `expert_data.json`
        - 所有专家数据自动保存
        - 支持关闭页面后数据不丢失
        - 支持多位专家协作分析
        """)


if __name__ == "__main__":
    main()
