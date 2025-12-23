import asyncio
import yt_dlp
import psutil
import os
from concurrent.futures import ThreadPoolExecutor

class RobustDownloader:
    def __init__(self, max_concurrent=5):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.executor = ThreadPoolExecutor(max_workers=20)
        self.pids = {} 
        self.is_cancelled = {}

    def progress_hook(self, d, video_id):
        if self.is_cancelled.get(video_id):
            raise Exception("STOP_NOW")

    def _run_download(self, url, video_id, opts):
        self.pids[video_id] = os.getpid() 
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
            return "Success"
        except Exception as e:
            if "STOP_NOW" in str(e) or self.is_cancelled.get(video_id):
                return "Cancelled"
            return f"Error: {str(e)}"

    async def download(self, video_id, url, save_path, resolution):
        """
        resolution: "1080", "720", "480" vb. değerler alır.
        """
        async with self.semaphore:
            self.is_cancelled[video_id] = False
            
            # FORMAT MANTIĞI:
            # 1. En iyi videoyu seç (seçilen çözünürlükten büyük olmasın ve mp4 olsun) + En iyi sesi seç (m4a olsun)
            # 2. EĞER yukarıdaki yoksa, direkt içinde ses olan en iyi MP4'ü indir (genelde 720p altı için)
            # 3. O da yoksa en iyisini indir.
            format_str = (
                # 1. Tercih: Seçilen yükseklikte MP4 video + M4A ses (En ideali)
                f"bestvideo[height<={resolution}][ext=mp4]+bestaudio[ext=m4a]/"
                # 2. Tercih: MP4 bulamazsan, seçilen yükseklikte herhangi bir format (WebM vb.) + Ses
                f"bestvideo[height<={resolution}]+bestaudio/"
                # 3. Tercih: Sesle birleşik halde gelen en iyi MP4
                f"best[height<={resolution}][ext=mp4]/"
                # 4. Tercih: Hiçbiri olmazsa seçilen çözünürlükteki en iyi dosya
                f"best[height<={resolution}]"
            )

            ydl_opts = {
                'format': format_str,
                'outtmpl': f'{save_path}/%(title)s.%(ext)s',
                'progress_hooks': [lambda d: self.progress_hook(d, video_id)],
                'quiet': True,
                'merge_output_format': 'mp4', # Ayrı inenleri mp4 çatısında birleştirir
            }

            loop = asyncio.get_running_loop()
            try:
                result = await loop.run_in_executor(
                    self.executor, self._run_download, url, video_id, ydl_opts
                )
                return result
            finally:
                self.pids.pop(video_id, None)
                self.is_cancelled.pop(video_id, None)

    def cancel(self, video_id):
        self.is_cancelled[video_id] = True
        parent_pid = self.pids.get(video_id)
        if parent_pid:
            self._kill_child_processes(parent_pid)

    def _kill_child_processes(self, parent_pid):
        try:
            parent = psutil.Process(parent_pid)
            for child in parent.children(recursive=True):
                child.kill()
        except psutil.NoSuchProcess:
            pass