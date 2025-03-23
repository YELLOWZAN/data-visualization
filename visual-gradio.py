import gradio as gr
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
from io import BytesIO
import tempfile
import os
import platform

# 字体配置
try:
    if platform.system() == 'Windows':
        plt.rcParams['font.sans-serif'] = ['SimHei']  # Windows
    elif platform.system() == 'Darwin':
        plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']  # Mac
    else:
        plt.rcParams['font.sans-serif'] = ['WenQuanYi Zen Hei']  # Linux
        
    plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
    
    # 加载字体
    matplotlib.font_manager.findfont('SimHei', rebuild_if_missing=True)
except Exception as e:
    print(f"字体设置失败: {e}")

# 缓存管理（chrome可能存在缓存爆炸问题）
temp_dir = tempfile.mkdtemp()
current_chart = None

def process_file(file):
    try:
        df = pd.read_excel(file)
        # 数据预处理
        if '日期' in df.columns:
            df['日期'] = pd.to_datetime(df['日期'])
        return df
    except Exception as e:
        print(f"文件处理错误: {e}")
        return None

def generate_chart(df, chart_type):
    global current_chart
    plt.figure(figsize=(10, 6), dpi=120)
    
    try:
        if chart_type == "柱状图":
            df_group = df.groupby('工作类型')['工作时长'].sum().reset_index()
            plt.bar(df_group['工作类型'], df_group['工作时长'])
            plt.title('各工作类型总时长统计', fontsize=12)
            plt.xlabel('工作类型', fontsize=10)
            plt.ylabel('总时长（小时）', fontsize=10)
            plt.xticks(rotation=45)
            
        # 本部分存在并发卡死bug，待日后修复
        elif chart_type == "折线图":
            df_group = df.groupby('日期')['工作时长'].sum().reset_index()
            plt.plot(df_group['日期'], df_group['工作时长'], 
                    marker='o', linestyle='--', linewidth=2)
            plt.title('每日工作时长趋势', fontsize=12)
            plt.xlabel('日期', fontsize=10)
            plt.ylabel('总时长（小时）', fontsize=10)
            plt.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            
        elif chart_type == "饼图":
            df_group = df.groupby('工作类型')['工作时长'].sum().reset_index()
            plt.pie(df_group['工作时长'], 
                   labels=df_group['工作类型'],
                   autopct='%1.1f%%',
                   startangle=90,
                   textprops={'fontsize': 8})
            plt.title('工作类型分布比例', fontsize=12)
            
        plt.tight_layout()
        
        # 保存图表
        chart_path = os.path.join(temp_dir, f'chart_{chart_type}.png')
        plt.savefig(chart_path, bbox_inches='tight', dpi=150)
        plt.close()
        
        current_chart = chart_path
        return chart_path
    
    except Exception as e:
        print(f"图表生成错误: {e}")
        return None

def update_ui(file, chart_type):
    try:
        if not file:
            return None, gr.update(interactive=False)
        
        df = process_file(file)
        if df is None or df.empty:
            return None, gr.update(interactive=False)
        
        chart_path = generate_chart(df, chart_type)
        return chart_path, gr.update(interactive=True)
    
    except Exception as e:
        print(f"界面更新错误: {e}")
        return None, gr.update(interactive=False)

# 构建Gradio界面
with gr.Blocks(title="工作数据分析仪") as demo:
    gr.Markdown("# 数据分析工具")
    
    with gr.Row():
        # 左侧上传区域
        with gr.Column(scale=1):
            file_input = gr.File(
                label="上传Excel文件",
                type="filepath",
                file_types=[".xlsx", ".xls"]
            )
        
        # 中间控制区域
        with gr.Column(scale=1):
            chart_type = gr.Radio(
                choices=["柱状图", "折线图", "饼图"],
                label="选择图表类型",
                value="柱状图"
            )
            generate_btn = gr.Button("生成图表", variant="primary")
        
        # 右侧展示区域
        with gr.Column(scale=2):
            chart_output = gr.Image(
                label="生成的图表",
                interactive=False,
                show_download_button=False
            )
            download_btn = gr.Button("下载图片", interactive=False)
    
    # 事件绑定
    generate_btn.click(
        fn=update_ui,
        inputs=[file_input, chart_type],
        outputs=[chart_output, download_btn]
    )
    
    download_btn.click(
        fn=lambda: current_chart if current_chart else None,
        outputs=gr.File(label="下载图表文件")
    )

if __name__ == "__main__":
    demo.launch(show_error=True)