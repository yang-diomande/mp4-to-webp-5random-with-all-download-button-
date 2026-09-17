import streamlit as st
import tempfile
import os
import subprocess
import random
import base64

st.set_page_config(page_title="MP4 to WebP 일괄 변환기 (랜덤 파일명)", page_icon="🎲", layout="centered")

st.title("🎲 MP4 ➔ WebP 일괄 변환기 (랜덤 파일명)")
st.write("여러 MP4 파일을 선택하면 `10000XXXXX.webp` 형태의 무작위 파일명으로 일괄 변환합니다.")

# 세션 상태 초기화 (다운로드 시 화면 리셋 방지용)
if "converted_files" not in st.session_state:
    st.session_state.converted_files = []

# 여러 파일 선택 지원
uploaded_files = st.file_uploader(
    "변환할 MP4 파일들을 선택하거나 드래그하세요 (여러 개 선택 가능)", 
    type=["mp4"], 
    accept_multiple_files=True
)

if uploaded_files:
    st.info(f"📁 총 {len(uploaded_files)}개의 파일이 선택되었습니다.")
    
    if st.button("🚀 랜덤 파일명으로 전체 변환 시작", type="primary", use_container_width=True):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        temp_dir = tempfile.mkdtemp()
        st.session_state.converted_files = []

        # 5자리 랜덤 시작 번호 생성 (첫 자리가 0이 안 나오도록 10000 ~ 99999)
        start_rand_num = random.randint(10000, 99999)

        for idx, uploaded_file in enumerate(uploaded_files):
            # 10000 + 순차 증가 5자리 숫자 생성
            current_num = start_rand_num + idx
            
            # 99999를 넘어가면 10000부터 다시 돌도록 오버플로우 처리
            if current_num > 99999:
                current_num = 10000 + (current_num - 100000)
                
            output_name = f"10000{current_num}.webp"

            status_text.text(f"⏳ [{idx + 1}/{len(uploaded_files)}] 변환 중: {uploaded_file.name} ➔ {output_name}")
            
            tmp_input_path = os.path.join(temp_dir, uploaded_file.name)
            with open(tmp_input_path, "wb") as f:
                f.write(uploaded_file.read())

            output_path = os.path.join(temp_dir, output_name)

            try:
                cmd = [
                    'ffmpeg',
                    '-y',
                    '-i', tmp_input_path,
                    '-vcodec', 'libwebp',
                    '-filter:v', 'fps=fps=min(source_fps\,30)',
                    '-lossless', '0',
                    '-q:v', '53',
                    '-preset', 'default',
                    '-loop', '0',
                    output_path
                ]
                
                subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    with open(output_path, "rb") as f:
                        file_bytes = f.read()
                    file_size_mb = round(len(file_bytes) / (1024 * 1024), 2)
                    
                    st.session_state.converted_files.append((output_name, uploaded_file.name, file_bytes, file_size_mb))

            except Exception as e:
                st.error(f"❌ {uploaded_file.name} 변환 실패: {e}")

            progress_bar.progress((idx + 1) / len(uploaded_files))

        status_text.empty()
        progress_bar.empty()

# 변환 결과 출력
if st.session_state.converted_files:
    st.success(f"🎉 총 {len(st.session_state.converted_files)}개 파일 변환 및 5자리 랜덤 파일명 지정 완료!")
    st.markdown("---")
    
    # -------------------------------------------------------------
    # [신규 기능] ZIP 없이 WebP 개별 파일들을 한 번에 순차 다운로드
    # -------------------------------------------------------------
    st.subheader("📦 전체 일괄 다운로드")
    
    if st.button("⚡ 변환된 WebP 전체 한 번에 다운로드", use_container_width=True, type="secondary"):
        # 자바스크립트로 파일들을 0.3초 간격으로 연속 다운로드 Trigger
        js_code = "<script>\n"
        for idx, (output_name, _, file_bytes, _) in enumerate(st.session_state.converted_files):
            b64 = base64.b64encode(file_bytes).decode()
            js_code += f"""
            setTimeout(function() {{
                var a = document.createElement('a');
                a.href = 'data:image/webp;base64,{b64}';
                a.download = '{output_name}';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
            }}, {idx * 300});
            """
        js_code += "</script>"
        st.components.v1.html(js_code, height=0)

    st.markdown("---")
    st.subheader("📥 개별 다운로드 목록")

    for idx, (output_name, orig_name, file_bytes, file_size_mb) in enumerate(st.session_state.converted_files):
        st.write(f"**{idx + 1}. {output_name}** (원본: `{orig_name}` / {file_size_mb} MB)")
        st.download_button(
            label=f"📥 {output_name} 다운로드",
            data=file_bytes,
            file_name=output_name,
            mime="image/webp",
            key=f"rand_download_{idx}_{output_name}",
            use_container_width=True
        )
