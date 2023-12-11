import subprocess
import sys
import os
import re
import argparse
import threading
import time
import json
# 内部スレッド数の定義
SCRIPT_THREAD_COUNT = 2
# エンコード中および完了したファイル数を追跡する変数を追加
encoding_count = 0
completed_count = 0

threads = []  # スレッドを格納するためのリスト

def load_config(config_file):
    with open(config_file, 'r', encoding='utf-8') as file:
        return json.load(file)



def get_ffmpeg_command():
    return os.environ.get('FFMPEG', 'ffmpeg')

def get_bitrate(ffmpeg, input_file):
    args = [ffmpeg, '-i', input_file]
    process = subprocess.Popen(args, stderr=subprocess.PIPE, text=True, encoding='utf-8')
    for line in process.stderr:
        if 'bitrate' in line:
            bitrate_match = re.search('bitrate: (\d+) kb/s', line)
            if bitrate_match:
                return int(bitrate_match.group(1))
    process.wait()
    return 0

def get_video_filter(resolution):
    if not resolution:
        return None
    filters = {
        '1080p': 'scale=-2:1080',
        '720p': 'scale=-2:720',
        '480p': 'scale=-2:480'
    }
    return filters.get(resolution)

def show_progress():
    global encoding_count, completed_count, threads
    while encoding_count > completed_count:
        print(f'進捗状況: {completed_count}/{encoding_count} ファイルが完了しました。')
        print(f'残り: {encoding_count - completed_count} ファイル')
        print("スレッド数: " + int(threading.active_count())-SCRIPT_THREAD_COUNT+"個")
        time.sleep(5)
        
def determine_encoding_parameters(input_bitrate, quality, input_file):
    ts_factor = 20 if input_file.endswith('.ts') else 2
    quality_settings = {
        'low': (ts_factor * 10, 'disabled'),
        'middle': (ts_factor * 5, 'middle'),
        'high': (ts_factor * 2.5, 'each'),
        'super': (2, 'each')
    }
    factor, b_ref_mode = quality_settings.get(quality, (2, 'each'))
    return input_bitrate / factor, b_ref_mode

def encode_video(ffmpeg, input_file, output_file, input_bitrate, quality, resolution, overwrite=False, codec=None):
    global completed_count
    if os.path.exists(output_file) and not overwrite:
        print(f'出力ファイルが既に存在します: {output_file}')
        completed_count += 1
        return
        
    output_bitrate, b_ref_mode = determine_encoding_parameters(input_bitrate, quality, input_file)
    video_filter = get_video_filter(resolution)

    args = [ffmpeg, '-i', input_file, '-c:v', codec, '-b:v', f'{output_bitrate}k', 
            '-b_ref_mode', b_ref_mode, '-f', 'mp4', '-tag:v', 'hvc1','-y']

    if video_filter:
        args.extend(['-vf', video_filter])
    args.append(output_file)

    print(f'実行コマンド: {" ".join(args)}')
    subprocess.Popen(args).wait()
    completed_count += 1
def get_args():
    content = {}
    try:
        # デフォルト値を読み込む
        config = load_config('config.json')
    except:
        print('config.jsonが見つかりませんでした。')
        # デフォルト値が読み込めない場合のデフォルト値
        config = {
            'input_dir': 'input',
            'output_dir': 'output',
            'quality': 'high',
            'resolution': 'None',
            'overwrite': False,
            'delete': True,
            'codec': 'hevc_nvenc'
        }
    input_dir = config['input_dir']
    output_dir = config['output_dir']
    quality = config['quality']
    resolution = config['resolution']
    if resolution == 'None':
        resolution = None
    overwrite = config['overwrite']
    delete = config['delete']
    codec = config['codec']
    parser = argparse.ArgumentParser(description='動画ファイルのエンコードスクリプト')
    parser.add_argument('-i', '--input_dir', help='入力ディレクトリパス',default = input_dir)
    parser.add_argument('-o', '--output_dir', default=output_dir, help='出力ディレクトリパス')
    parser.add_argument('-q', '--quality', default=quality, choices=['low', 'middle', 'high', 'super'], help='エンコード品質')
    parser.add_argument('-r', '--resolution', help='解像度 (例: 1080p, 720p, 480p)', default=resolution,choices=['1080p', '720p', '480p'])
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 1.0.0')
    parser.add_argument('-w','--overwrite', action='store_true', help='出力先に同じ名前のファイルがある場合既存のファイルを上書きする', default=overwrite)
    parser.add_argument('-d', '--delete', action='store_true', help='エンコード後に元ファイルを削除する', default=delete)
    parser.add_argument('-c', '--codec', help='使用するコーデック', default=codec)
    args = parser.parse_args()
    content['input_dir'] = args.input_dir
    content['output_dir'] = args.output_dir
    content['quality'] = args.quality
    content['resolution'] = args.resolution
    content['overwrite'] = args.overwrite
    content['delete'] = args.delete
    content['codec'] = args.codec
    return content
def main(input_dir=None, output_dir=None, quality=None, resolution=None, delete=True, overwrite=False, codec=None):
    global encoding_count
    global threads
    #もし関数事態に引数がない場合はコマンドライン引数を取得（コマンドにも引数がない場合はデフォルト値を使用）
    if input_dir==None:
        args = get_args()
        input_dir = args['input_dir']
        output_dir = args['output_dir']
        quality = args['quality']
        resolution = args['resolution']
        delete = args['delete']
        overwrite = args['overwrite']
        codec = args['codec']
    max_threads = 6 #最大スレッド数(使用しているGPUによって変更する)
    ffmpeg = get_ffmpeg_command()
    input_files = [os.path.join(input_dir, file_name) for file_name in os.listdir(input_dir)]
    input_files = [file_name for file_name in input_files if os.path.isfile(file_name) and file_name.endswith(('.mp4', '.ts'))]
    #設定
    print("入力パス: " + input_dir)
    print("出力パス: " + output_dir)
    print("エンコード品質: " + quality)
    if resolution==None:
        print("解像度: そのまま")
    else:
        print("解像度: " + resolution)
    print("元ファイル削除: " + str(delete))
    print('入力ファイル: ')
    print("コーデック: " + codec)
    #入力ファイル表示とエンコードリスト作成
    encode_list = []
    for input_file in input_files:
        print(input_file)
        encode_list.append(input_file)
    encoding_count = len(input_files)
    if encoding_count == 0:
        print('エンコードするファイルがありません。')
        return
    print(f"合計: {encoding_count} ファイル")
    while True:
        answer = input('上記のファイルをエンコードしますか？ [y/n]: ')
        if answer in ('y'):
            break
        elif answer in ('n'):
            print('エンコードを中止します。')
            return
        else:
            print('yかnで答えてください。')
    # 進捗状況を表示するスレッドを開始
    progress_thread = threading.Thread(target=show_progress)
    progress_thread.start()
    #出力先ディレクトリ作成
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    
    for input_file in input_files:
        input_bitrate = get_bitrate(ffmpeg, input_file)
        output_file = os.path.join(output_dir, os.path.basename(input_file))
        # encode_video(ffmpeg, input_file, output_file, input_bitrate, quality, resolution, overwrite)
        #スレッド処理
        while True:
            if threading.active_count() < max_threads:
                thread = threading.Thread(target=encode_video, args=(ffmpeg, input_file, output_file, input_bitrate, quality, resolution, overwrite, codec))
                thread.start()
                threads.append(thread)  # スレッドをリストに追加
                break
            else:
                time.sleep(1)  # アクティブなスレッドの数が最大に達している場合、少し待機
    # すべてのスレッドが終了するのを待つ
    for thread in threads:
        thread.join()
    # 進捗表示スレッドが終了するのを待つ
    progress_thread.join()
    # if delete:
    #     print('元ファイルを削除中...')
    #     for input_file in input_files:
    #         os.remove(input_file).
    if delete:
        print('元ファイルを削除中...')
        for input_file in input_files:
            os.remove(input_file)
            
            
    print('エンコードが完了しました。')

if __name__ == "__main__":
    main()
