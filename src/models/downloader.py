import asyncio
import yt_dlp
import psutil
import os
from concurrent.futures import ThreadPoolExecutor
import glob

class RobustDownloader:
    def __init__(self, max_concurrent=5):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.executor = ThreadPoolExecutor(max_workers=20)
        self.processes = {}  # video_id: psutil.Process (Ana süreçleri tutar)
        self.is_cancelled = {}
        self.latest_progress = {}

    def progress_hook(self, d, video_id):
        # yt-dlp içinden iptal kontrolü
        if self.is_cancelled.get(video_id):
            raise Exception("STOP_NOW")
        
        if d['status'] == 'downloading':
            try:
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                downloaded = d.get('downloaded_bytes', 0)
                speed = d.get('speed', 0)
                eta = d.get('eta', 0)
                
                self.latest_progress[video_id] = {
                    'status': 'downloading',
                    'downloaded': downloaded,
                    'total': total,
                    'percentage': (downloaded / total * 100) if total > 0 else 0,
                    'speed': speed,
                    'eta': eta
                }
            except:
                pass

    def _run_download(self, url, video_id, opts):
        try:
            opts_with_hook = opts.copy()
            opts_with_hook['progress_hooks'] = [lambda d: self.progress_hook(d, video_id)]
            
            with yt_dlp.YoutubeDL(opts_with_hook) as ydl:
                # Çalışan mevcut Python sürecini (ve dolayısıyla alt süreçlerini) takip için kaydet
                self.processes[video_id] = psutil.Process(os.getpid())
                ydl.download([url])
            return "Success"
        except Exception as e:
            if "STOP_NOW" in str(e) or self.is_cancelled.get(video_id):
                return "Cancelled"
            return f"Error: {str(e)}"
        finally:
            self.processes.pop(video_id, None)

    async def download(self, video_id, url, save_path, resolution="1080", progress_callback=None):
        async with self.semaphore:
            self.is_cancelled[video_id] = False
            self.latest_progress[video_id] = {}
            
            ydl_opts = {
                'format': f"bestvideo[height<={resolution}][ext=mp4]+bestaudio[ext=m4a]/best[height<={resolution}][ext=mp4]/best",
                'outtmpl': f'{save_path}/%(title)s.%(ext)s',
                'quiet': True,
                'merge_output_format': 'mp4',
            }
            
            loop = asyncio.get_running_loop()
            monitor_task = asyncio.create_task(self._monitor_progress(video_id, progress_callback)) if progress_callback else None
            
            try:
                result = await loop.run_in_executor(self.executor, self._run_download, url, video_id, ydl_opts)
                return result
            finally:
                if monitor_task:
                    monitor_task.cancel()
                self.is_cancelled.pop(video_id, None)

    async def _monitor_progress(self, video_id, callback):
        try:
            while True:
                await asyncio.sleep(0.4)
                if video_id in self.latest_progress:
                    data = self.latest_progress[video_id]
                    if data: callback(data)
        except asyncio.CancelledError:
            pass

    async def cancel(self, video_id):
        """Hiyerarşik (ffmpeg dahil) ve asenkron iptal"""
        self.is_cancelled[video_id] = True
        process = self.processes.get(video_id)
        
        if process:
            loop = asyncio.get_running_loop()
            # İşletim sistemi seviyesindeki ağır kill işlemini executor ile yap
            await loop.run_in_executor(None, self._force_kill_recursive, process)
            self.processes.pop(video_id, None)
        
        await asyncio.sleep(0.3)
        self._cleanup_temp_files()

    def _force_kill_recursive(self, process):
        """ffmpeg ve tüm alt süreçleri kesin olarak öldürür"""
        try:
            # recursive=True: yt-dlp'nin başlattığı ffmpeg gibi tüm alt süreçleri bulur
            children = process.children(recursive=True)
            for child in children:
                try:
                    child.kill() # Acıma yok, doğrudan durdur
                except:
                    pass
            # Ana işlem hattını durdurmaya çalış (isteğe bağlı, thread sonlanması için)
            # process.terminate() 
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    def _cleanup_temp_files(self):
        patterns = ['*.part', '*.ytdl', '*.temp', '*.f*-*.m4a', '*.f*-*.mp4']
        for p in patterns:
            for f in glob.glob(p):
                try: os.remove(f)
                except: pass