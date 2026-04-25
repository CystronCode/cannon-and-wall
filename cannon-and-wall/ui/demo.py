import gradio as gr
from client.client import CannonWallClient

client = CannonWallClient()

def start_round(stage):
    obs = client.reset(stage=int(stage))
    return obs["source_code"], "Round started. Source loaded.", ""

def get_scores():
    s = client.state()
    scores = s.get("scores", {})
    return f"Cannon: {scores.get('cannon',0)} | Wall: {scores.get('wall',0)} | Round: {s.get('round',1)}"

with gr.Blocks() as demo:
    with gr.Tab("Run Episode"):
        stage_dd = gr.Dropdown([1,2,3], value=1, label="Stage")
        start_btn = gr.Button("Start Round")
        source_box = gr.Textbox(label="Source Code", lines=20)
        status_box = gr.Textbox(label="Status")
        output_box = gr.Textbox(label="Agent Output")
        start_btn.click(start_round, inputs=[stage_dd], outputs=[source_box, status_box, output_box])
    with gr.Tab("Scores"):
        score_btn = gr.Button("Refresh Scores")
        score_box = gr.Textbox(label="Current Scores")
        score_btn.click(get_scores, outputs=[score_box])

if __name__ == "__main__":
    demo.launch(server_port=7861)
