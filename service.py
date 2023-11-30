import subprocess
import sys
import os
import re
import argparse

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

def determine_encoding_parameters(input_bitrate, quality, input_file):
    ts_factor = 20 if input_file.endswith('.ts') else 2
    quality_settings = {
        'low': (ts_factor * 10, 'disabled'),
        'middle': (ts_factor * 5, 'middle'),
        'high': (ts_factor * 2.5, 'each'),
        'super': (2, 'each')
    }
    factor, b_ref_mode = quality_settings.get(quality, (2, 'middle'))
    return input_bitrate / factor, b_ref_mode

def encode_video(ffmpeg, input_file, output_file, input_bitrate, quality, resolution, overwrite=False):
    if os.path.exists(output_file) and not overwrite:
        print(f'出力ファイルが既に存在します: {output_file}')
        return
        
    output_bitrate, b_ref_mode = determine_encoding_parameters(input_bitrate, quality, input_file)
    video_filter = get_video_filter(resolution)

    args = [ffmpeg, '-i', input_file, '-c:v', 'hevc_nvenc', '-b:v', f'{output_bitrate}k', 
            '-b_ref_mode', b_ref_mode, '-f', 'mp4', '-tag:v', 'hvc1','-y']

    if video_filter:
        args.extend(['-vf', video_filter])
    args.append(output_file)

    print(f'実行コマンド: {" ".join(args)}')
    subprocess.Popen(args).wait()

def get_args():
    content = {}
    parser = argparse.ArgumentParser(description='動画ファイルのエンコードスクリプト')
    parser.add_argument('-i', '--input_dir', help='入力ディレクトリパス',default = os.getcwd())
    parser.add_argument('-o', '--output_dir', default=os.path.join(os.getcwd(), 'output'), help='出力ディレクトリパス')
    parser.add_argument('-q', '--quality', default='middle', choices=['low', 'middle', 'high', 'super'], help='エンコード品質')
    parser.add_argument('-r', '--resolution', help='解像度 (例: 1080p, 720p, 480p)', default=None,choices=['1080p', '720p', '480p'])
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 1.0.0')
    parser.add_argument('-w','--overwrite', action='store_true', help='出力先に同じ名前のファイルがある場合既存のファイルを上書きする', default=False)
    parser.add_argument('-d', '--delete', action='store_true', help='エンコード後に元ファイルを削除する', default=True)
    args = parser.parse_args()
    content['input_dir'] = args.input_dir
    content['output_dir'] = args.output_dir
    content['quality'] = args.quality
    content['resolution'] = args.resolution
    content['overwrite'] = args.overwrite
    content['delete'] = args.delete
    return content
def main(input_dir=None, output_dir=None, quality=None, resolution=None, delete=True, overwrite=False):
    if input_dir==None:
        args = get_args()
        input_dir = args['input_dir']
        output_dir = args['output_dir']
        quality = args['quality']
        resolution = args['resolution']
        delete = args['delete']
        overwrite = args['overwrite']


    ffmpeg = get_ffmpeg_command()
    input_files = [os.path.join(input_dir, file_name) for file_name in os.listdir(input_dir)]
    input_files = [file_name for file_name in input_files if os.path.isfile(file_name) and file_name.endswith(('.mp4', '.ts'))]
    #設定
    print("出力パス: " + output_dir)
    print("エンコード品質: " + quality)
    if resolution==None:
        print("解像度: そのまま")
    else:
        print("解像度: " + resolution)
    print("元ファイル削除: " + str(delete))
    print('入力ファイル: ')
    for input_file in input_files:
        print(input_file)
    
    while True:
        answer = input('上記のファイルをエンコードしますか？ [y/n]: ')
        if answer in ('y'):
            break
        elif answer in ('n'):
            print('エンコードを中止します。')
            return
        else:
            print('yかnで答えてください。')
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    for input_file in input_files:
        input_bitrate = get_bitrate(ffmpeg, input_file)
        output_file = os.path.join(output_dir, os.path.basename(input_file))
        encode_video(ffmpeg, input_file, output_file, input_bitrate, quality, resolution, overwrite)
        if delete:
            print('元ファイルを削除中...')
            os.remove(input_file)
    # if delete:
    #     print('元ファイルを削除中...')
    #     for input_file in input_files:
    #         os.remove(input_file)
    print('エンコードが完了しました。')

if __name__ == "__main__":
    main()
