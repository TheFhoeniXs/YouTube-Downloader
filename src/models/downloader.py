import asyncio
import yt_dlp
import psutil
import os
from concurrent.futures import ThreadPoolExecutor
import glob


class DynamicSemaphore:
    """Dinamik olarak değer değiştirilebilen semaphore"""
    
    def __init__(self, value=1):
        self._value = value
        self._waiters = []
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        """Semaphore'u kilitle"""
        async with self._lock:
            # Eğer slot varsa hemen al
            if self._value > 0:
                self._value -= 1
                return
            
            # Slot yoksa bekle
            fut = asyncio.get_event_loop().create_future()
            self._waiters.append(fut)
        
        # Lock dışında bekle
        try:
            await fut
        except asyncio.CancelledError:
            async with self._lock:
                # İptal edilirse slot'u geri ver
                if not fut.done():
                    self._waiters.remove(fut)
                else:
                    # Future zaten tamamlanmışsa, slot'u geri ver
                    self._value += 1
            raise
    
    def release(self):
        """Semaphore'u serbest bırak"""
        async def _release():
            async with self._lock:
                self._value += 1
                # Bekleyen varsa uyandır
                while self._waiters and self._value > 0:
                    fut = self._waiters.pop(0)
                    if not fut.done():
                        self._value -= 1
                        fut.set_result(None)
                        break
        
        asyncio.create_task(_release())
    
    async def set_value(self, new_value):
        """Dinamik olarak maksimum değeri değiştir"""
        async with self._lock:
            old_value = self._value
            self._value = new_value
            
            # Eğer limit artırıldıysa, bekleyen task'ları uyandır
            if new_value > old_value:
                wake_count = new_value - old_value
                for _ in range(wake_count):
                    if self._waiters and self._value > 0:
                        fut = self._waiters.pop(0)
                        if not fut.done():
                            self._value -= 1
                            fut.set_result(None)
    
    async def get_value(self):
        """Mevcut değeri döndür"""
        async with self._lock:
            return self._value
    
    def get_waiting_count(self):
        """Bekleyen task sayısını döndür"""
        return len(self._waiters)
    
    async def __aenter__(self):
        await self.acquire()
        return self
    
    async def __aexit__(self, exc_type, exc, tb):
        self.release()


class RobustDownloader:
    def __init__(self, max_concurrent=5):
        self.max_concurrent = max_concurrent
        self.semaphore = DynamicSemaphore(max_concurrent)
        self.executor = ThreadPoolExecutor(max_workers=20)
        self.processes = {}
        self.is_cancelled = {}
        self.latest_progress = {}
        self.active_downloads = 0
        self._stats_lock = asyncio.Lock()

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
        # Semaphore'u bekle
        await self.semaphore.acquire()
        
        try:
            async with self._stats_lock:
                self.active_downloads += 1
            
            self.is_cancelled[video_id] = False
            self.latest_progress[video_id] = {}
            
            ydl_opts = {
                'format': f"bestvideo[height<={resolution}][ext=mp4]+bestaudio[ext=m4a]/best[height<={resolution}][ext=mp4]/best",
                'outtmpl': f'{save_path}/%(title)s_{resolution}p.%(ext)s',
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
                    try:
                        await monitor_task
                    except asyncio.CancelledError:
                        pass
                
                self.is_cancelled.pop(video_id, None)
        finally:
            async with self._stats_lock:
                self.active_downloads -= 1
            
            # Semaphore'u serbest bırak
            self.semaphore.release()

    async def _monitor_progress(self, video_id, callback):
        try:
            while True:
                await asyncio.sleep(0.4)
                if video_id in self.latest_progress:
                    data = self.latest_progress[video_id]
                    if data: 
                        callback(data)
        except asyncio.CancelledError:
            pass

    async def cancel(self, video_id):
        """Hiyerarşik (ffmpeg dahil) ve asenkron iptal"""
        self.is_cancelled[video_id] = True
        process = self.processes.get(video_id)
        
        if process:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._force_kill_recursive, process)
            self.processes.pop(video_id, None)
        
        await asyncio.sleep(0.3)
        #self._cleanup_temp_files()

    def _force_kill_recursive(self, process):
        """ffmpeg ve tüm alt süreçleri kesin olarak öldürür"""
        try:
            children = process.children(recursive=True)
            for child in children:
                try:
                    child.kill()
                except:
                    pass
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    def _cleanup_temp_files(self):
        patterns = ['*.part', '*.ytdl', '*.temp', '*.f*-*.m4a', '*.f*-*.mp4']
        for p in patterns:
            for f in glob.glob(p):
                try: 
                    os.remove(f)
                except: 
                    pass
    
    # ============== DİNAMİK YÖNETİM FONKSİYONLARI ==============
    
    async def set_max_concurrent(self, new_limit):
        """
        Maksimum eşzamanlı indirme sayısını dinamik olarak değiştirir.
        
        Önemli: Limit azaltılırsa, devam eden indirmeler tamamlanır
        ama yenileri bekletilir. Artırılırsa bekleyenler hemen başlatılır.
        """
        async with self._stats_lock:
            old_limit = self.max_concurrent
            self.max_concurrent = new_limit
            
            # Semaphore değerini güncelle
            current_available = await self.semaphore.get_value()
            
            # Yeni available slot sayısını hesapla
            # available = new_limit - active_downloads
            new_available = max(0, new_limit - self.active_downloads)
            
            await self.semaphore.set_value(new_available)
            
            print(f"✅ Max concurrent: {old_limit} -> {new_limit}")
            print(f"   Aktif indirmeler: {self.active_downloads}")
            print(f"   Mevcut slotlar: {current_available} -> {new_available}")
            print(f"   Bekleyen indirmeler: {self.semaphore.get_waiting_count()}")
    
    async def get_stats(self):
        """Downloader istatistiklerini döndürür"""
        async with self._stats_lock:
            current_value = await self.semaphore.get_value()
            return {
                'max_concurrent': self.max_concurrent,
                'active_downloads': self.active_downloads,
                'waiting_downloads': self.semaphore.get_waiting_count(),
                'available_slots': current_value,
                'total_tracked': len(self.processes),
            }
    
    async def increase_limit(self, amount=1):
        """Limiti belirli miktarda artırır"""
        new_limit = self.max_concurrent + amount
        await self.set_max_concurrent(new_limit)
    
    async def decrease_limit(self, amount=1):
        """Limiti belirli miktarda azaltır (minimum 1)"""
        new_limit = max(1, self.max_concurrent - amount)
        await self.set_max_concurrent(new_limit)
    
    def get_active_downloads(self):
        """Aktif indirme sayısını senkron olarak döndürür"""
        return self.active_downloads
    
    def get_waiting_count(self):
        """Bekleyen indirme sayısını döndürür"""
        return self.semaphore.get_waiting_count()