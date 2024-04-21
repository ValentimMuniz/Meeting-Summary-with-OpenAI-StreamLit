import streamlit as st
import os 
from moviepy.editor import *
import tempfile
from vosk import Model, KaldiRecognizer
import json
from pydub import AudioSegment
from moviepy.editor import *
import wave
from openai import OpenAI 
from datetime import datetime
from pathlib import Path
import time
from streamlit_js_eval import streamlit_js_eval
import tiktoken


PROMPT = '''
Somos da empresa Yssy, empresa de tecnologia que atende diversas frentes.
Faça o resumo do texto delimitado por #### 
O texto é a transcrição de uma reunião.
Tente identificar se foi citado nesse texto de algum cliente e colocar no nome dele.
Se houver alguma data definida para alguma atividade ou próxima reuniao, colocar essa data no formato dd/MM/aaaa
O resumo deve contar com os principais assuntos abordados e separados por topico e bem detalhado.
O resumo deve estar em texto corrido.
O resumo deve contar com as soluções tecnologicas proposta.
No final, devem ser apresentados todos acordos,combinados e proximos passos
feitos na reunião no formato de bullet points.

O formato final que eu desejo é:

Resumo reunião:
- escrever aqui o resumo detalhado

Nome do cliente:
- escrever aqui o nome do cliente se foi identificado

Acordos da Reunião :
- acordo 1
- acordo 2
- acordo 3
- acordo n

Próximos passos :
- passo 1
- passo 2
- passo n


Soluções propostas:
- solução 1
- solução 2
- solução n

Data próximos passos ou reuinão:
- escrever aqui a data

texto: ####{}####
'''

#Funções para pegar quantos tokens vão ter na transcrição para decidir qual modelo usar dp OpenAIcd
def encoding_getter(encoding_type: str):
    """
    Returns the appropriate encoding based on the given encoding type (either an encoding string or a model name).
    """
    if "k_base" in encoding_type:
        return tiktoken.get_encoding(encoding_type)
    else:
        return tiktoken.encoding_for_model(encoding_type)

def tokenizer(string: str, encoding_type: str) -> list:
    """
    Returns the tokens in a text string using the specified encoding.
    """
    encoding = encoding_getter(encoding_type)
    tokens = encoding.encode(string)
    return tokens

def token_counter(string: str, encoding_type: str) -> int:
    """
    Returns the number of tokens in a text string using the specified encoding.
    """
    num_tokens = len(tokenizer(string, encoding_type))
    return num_tokens

def chat_openai(
        mensagem,
        modelo='gpt-4-turbo',
    ): 
    client = OpenAI(api_key="sk-proj-QaNTpeqK1xMGqMIIZM2LT3BlbkFJKVWNZPz7WbOsHH2szHe1")
    mensagens = [{'role': 'user', 'content': mensagem}]
    resposta = client.chat.completions.create(
        model=modelo,
        messages=mensagens,
        )
    return resposta.choices[0].message.content


def listar_reunioes():
    lista_reunioes = Path(PASTA_ARQUIVOS + "/reunioes").glob('*')
    lista_reunioes = list(lista_reunioes)
    lista_reunioes.sort(reverse=True)
    reunioes_dict = {}
    for pasta_reuniao in lista_reunioes:
        data_reuniao = Path(pasta_reuniao).stem
        
        ano, mes, dia, hora, min, seg = data_reuniao.split('_')
        reunioes_dict[data_reuniao] = f'{ano}/{mes}/{dia} {hora}:{min}:{seg}'
        titulo = le_arquivo(pasta_reuniao / 'titulo.txt')
        if titulo != '':
            reunioes_dict[data_reuniao] += f' - {titulo}'
    return reunioes_dict

# TAB SELEÇÃO REUNIÃO =====================
def tab_selecao_reuniao():
    reunioes_dict = listar_reunioes()
    if len(reunioes_dict) > 0:
        reuniao_selecionada = st.selectbox('Selecione uma reunião',
                                        list(reunioes_dict.values()))
        st.divider()
        reuniao_data = [k for k, v in reunioes_dict.items() if v == reuniao_selecionada][0]
        pasta_reuniao = PASTA_ARQUIVOS + "/reunioes/" + str(reuniao_data)
        if not os.path.exists(pasta_reuniao + '/titulo.txt'):
            st.warning('Adicione um titulo')
            titulo_reuniao = st.text_input('Título da reunião')
            st.button('Salvar',
                      on_click=salvar_titulo,
                      args=(pasta_reuniao, titulo_reuniao))
        else:
            titulo = le_arquivo(pasta_reuniao + '/titulo.txt')
            resumo = le_arquivo(pasta_reuniao + '/resumo.txt')
            st.markdown(f'## {titulo}')
            st.markdown(resumo)
    else:
        st.markdown("Sem reuniões")
    return
        
#Função para salvar título 
def salvar_titulo(pasta_reuniao, titulo):
    if titulo != "":
        salva_arquivo(pasta_reuniao + '/titulo.txt', titulo)
    else:
        st.warning('Por favor digite um titulo para a reunião', icon="⚠️")
    


def mp4_to_mp3(mp4FilePath, mp3FilePath, nomeArquivo, pasta_reuniao):  
    video = VideoFileClip(mp4FilePath) 
    audio = video.audio
    audio.write_audiofile(mp3FilePath)


    #pegar o .mp3 e corverter para WAV
    audioFromMP3 = AudioSegment.from_mp3(mp3FilePath)
    
    #criar um WAV do MP3
    fullWAVpath = pasta_reuniao + "/" + nomeArquivo + ".wav"
    audioFromMP3.export(fullWAVpath, format="wav")


    #Pegar o audio WAV convertido e transformar em MONO
    # Load audio file
    audiofromWAV = AudioSegment.from_wav(fullWAVpath)

    # Convert to mono
    audiofromWAV = audiofromWAV.set_channels(1)

    # Set frame rate 
    audiofromWAV = audiofromWAV.set_frame_rate(16000)
    fullMonoPathFile = pasta_reuniao + "/" + nomeArquivo + "_mono" + ".wav"
    # Save new audio
    audiofromWAV.export(fullMonoPathFile , format="wav")
        
    os.remove(mp3FilePath)
    os.remove(fullWAVpath)

    placeholder = st.empty()
    with placeholder, st.spinner('Transcrevendo áudio e gerando resumo...'):
        transcreve_audio(fullMonoPathFile, pasta_reuniao, placeholder)



def le_arquivo(caminho_arquivo):
   
    if os.path.exists(caminho_arquivo):
        with open(caminho_arquivo) as f:
            return f.read()
    else:
        return ''
    

def salva_arquivo(caminho_arquivo, conteudo):
    
    if not os.path.isfile(caminho_arquivo ):
        f = open(caminho_arquivo, "x")
        f.close()

    f = open(caminho_arquivo, "a")
    f.write(conteudo)
    f.close()


def transcreve_audio(caminho_audio, pasta_reuniao, placeholder):
    model = Model(PASTA_MODELO + "/vosk-model-pt-fb-v0.1.1-pruned")
    rec = KaldiRecognizer(model, 16000)

    # Open WAV file
    wf = wave.open(caminho_audio, "rb")

    # List to hold all text segments
    transcribed_text_list = []

    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            result = json.loads(rec.Result())
            transcribed_text_list.append(result['text'])
    # Handle last part of audio
    final_result = json.loads(rec.FinalResult())
    transcribed_text_list.append(final_result['text'])

    # Concatenate all text segments
    complete_text = ' '.join(transcribed_text_list)
    
    salva_arquivo(pasta_reuniao + "/transcricao.txt", complete_text) 

    gerar_resumo(complete_text, pasta_reuniao, placeholder)   
    

    
def gerar_resumo(transcricao, pasta_reuniao, placeholder):    
    
    #Mandar texto da transcrição pro OpenAI para fazer o resumo
    resumo = chat_openai(mensagem=PROMPT.format(transcricao))    

    #Salvar o arquivo com o resumo
    salva_arquivo(pasta_reuniao + "/resumo.txt", resumo)
    placeholder.empty()
    st.success('Resumo gerado, vá na aba de resumos e salve o titulo de seu resumo!')
    time.sleep(4)
    streamlit_js_eval(js_expressions="parent.window.location.reload(true)")


# Disable the submit button after it is clicked 
def disable(uploaded_file):
    if uploaded_file is not None:
        st.session_state.disabled = True
    
        
# Initialize disabled for form_submit_button to False
if "disabled" not in st.session_state:
    st.session_state.disabled = False


def tab_upload_reuniao():
    with st.form("my-form", clear_on_submit=True,border=True):
        uploaded_file = st.file_uploader("Faça upload da reunião (MP4)", type=(["mp4"]), accept_multiple_files=False)

        submit_button = st.form_submit_button(
            "Gerar resumo!", on_click=disable(uploaded_file), disabled=st.session_state.disabled, args=('Hi!')
        )

        if submit_button and uploaded_file is not None: 
            #criar arquivo temporario para o mp4
            temp_dir = tempfile.mkdtemp()
            mp4path = os.path.join(temp_dir, uploaded_file.name)
            with open(mp4path, "wb") as f: 
                    f.write(uploaded_file.getvalue())
                
            agora = str(datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
            #Criar pasta da reunião com data atual 
            pasta_reuniao = PASTA_ARQUIVOS + "/reunioes/" + agora
            
            fullFolderPath = os.path.expanduser(pasta_reuniao)
            if not os.path.exists(fullFolderPath):
                os.makedirs(fullFolderPath)

            renomeado = uploaded_file.name.replace('.mp4', '')

            fullmp3path = pasta_reuniao + "/" + renomeado + ".mp3"

            mp4_to_mp3(mp4path, fullmp3path, renomeado, pasta_reuniao)

        if submit_button and uploaded_file is None:
            st.warning('Por favor selecione um arquivo', icon="⚠️")
 
       


#Função principal do código
def main():
    #Definir pasta root dos arquivos
    global PASTA_ARQUIVOS, PASTA_MODELO
    PASTA_ARQUIVOS = os.path.expanduser("~") + "/.MeetGPT"
    PASTA_MODELO = os.path.expanduser("~") + "/.MeetGPT/models"
    #PASTA_ARQUIVOS = current_working_directory(__file__) + "/arquivos"


    #Criar diretorio na pasta root
    if not os.path.exists(PASTA_ARQUIVOS):
        os.makedirs(PASTA_ARQUIVOS)
    
    #Criar diretorio na pasta root
    if not os.path.exists(PASTA_MODELO):
        os.makedirs(PASTA_MODELO)

    st.header('Meeting GPT 🎙️', divider=True)
    tab_gravar, tab_selecao = st.tabs(['Gravar Reunião', 'Ver Resumos de reuniões'])
    with tab_gravar:
        tab_upload_reuniao()
    with tab_selecao:
        tab_selecao_reuniao()
    return
    
    
 
if __name__ == '__main__':
    main()
    
    



    
    

    
    