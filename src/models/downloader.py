import asyncio
import yt_dlp
import psutil
import os
from concurrent.futures import ThreadPoolExecutor
import glob
import signal
import sys


class DynamicSemaphore:
    """Dinamik olarak değer değiştirilebilen semaphore"""
    
    def __init__(self, value=1):
        self._value = value
        self._waiters = []
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        """Semaphore'u kilitle"""
        async with self._lock:
            if self._value > 0:
                self._value -= 1
                return
            
            fut = asyncio.get_event_loop().create_future()
            self._waiters.append(fut)
        
        try:
            await fut
        except asyncio.CancelledError:
            async with self._lock:
                if not fut.done():
                    self._waiters.remove(fut)
                else:
                    self._value += 1
            raise
    
    def release(self):
        """Semaphore'u serbest bırak"""
        async def _release():
            async with self._lock:
                self._value += 1
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
        
        # ✅ YENİ: Her video için ayrı cancel event
        self.cancel_events = {}

    def progress_hook(self, d, video_id):
        # ✅ Daha güvenli cancel kontrolü
        if self.is_cancelled.get(video_id, False):
            raise Exception("DOWNLOAD_CANCELLED_BY_USER")
        
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
            
            # ✅ Process'i kaydet
            current_process = psutil.Process(os.getpid())
            self.processes[video_id] = current_process
            
            with yt_dlp.YoutubeDL(opts_with_hook) as ydl:
                ydl.download([url])
            
            return "Success"
            
        except Exception as e:
            error_msg = str(e)
            # ✅ İptal durumunu daha iyi algıla
            if ("DOWNLOAD_CANCELLED_BY_USER" in error_msg or 
                "STOP_NOW" in error_msg or 
                self.is_cancelled.get(video_id, False)):
                return "Cancelled"
            return f"Error: {error_msg}"
            
        finally:
            # ✅ Process'i temizle
            self.processes.pop(video_id, None)

    async def download(self, video_id, url, save_path, resolution="1080", progress_callback=None):
        # Semaphore'u bekle
        await self.semaphore.acquire()
        
        try:
            async with self._stats_lock:
                self.active_downloads += 1
            
            # ✅ Cancel state'i başlat
            self.is_cancelled[video_id] = False
            self.cancel_events[video_id] = asyncio.Event()
            self.latest_progress[video_id] = {}
            
            ydl_opts = {
                'format': f"bestvideo[height<={resolution}][ext=mp4]+bestaudio[ext=m4a]/best[height<={resolution}][ext=mp4]/best",
                'outtmpl': f'{save_path}/%(title)s_{resolution}p.%(ext)s',
                'quiet': True,
                'merge_output_format': 'mp4',
            }
            
            loop = asyncio.get_running_loop()
            monitor_task = None
            
            if progress_callback:
                monitor_task = asyncio.create_task(
                    self._monitor_progress(video_id, progress_callback)
                )
            
            try:
                # ✅ Download işlemini başlat
                result = await loop.run_in_executor(
                    self.executor, 
                    self._run_download, 
                    url, 
                    video_id, 
                    ydl_opts
                )
                
                return result
                
            finally:
                # ✅ Monitor'u durdur
                if monitor_task:
                    monitor_task.cancel()
                    try:
                        await monitor_task
                    except asyncio.CancelledError:
                        pass
                
                # ✅ Cleanup
                self.is_cancelled.pop(video_id, None)
                self.cancel_events.pop(video_id, None)
                self.latest_progress.pop(video_id, None)
                
        finally:
            async with self._stats_lock:
                self.active_downloads -= 1
            
            self.semaphore.release()

    async def _monitor_progress(self, video_id, callback):
        """Progress monitoring loop"""
        try:
            while True:
                await asyncio.sleep(0.4)
                
                # ✅ İptal edildiyse dur
                if self.is_cancelled.get(video_id, False):
                    break
                
                if video_id in self.latest_progress:
                    data = self.latest_progress[video_id]
                    if data:
                        try:
                            callback(data)
                        except:
                            pass
                            
        except asyncio.CancelledError:
            pass

    async def cancel(self, video_id):
        """✅ Geliştirilmiş iptal mekanizması"""
        print(f"🛑 Downloader.cancel() çağrıldı: {video_id}")
        
        # 1. Flag'i set et (progress_hook için)
        self.is_cancelled[video_id] = True
        
        # 2. Event'i set et
        if video_id in self.cancel_events:
            self.cancel_events[video_id].set()
        
        # 3. Process'i öldür
        process = self.processes.get(video_id)
        if process:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._force_kill_recursive, process)
            self.processes.pop(video_id, None)
        
        # ✅ Daha uzun bekleme süresi - process'in tamamen ölmesi için
        await asyncio.sleep(1.0)
        
        print(f"✅ Downloader.cancel() tamamlandı: {video_id}")

    def _force_kill_recursive(self, process):
        """✅ Geliştirilmiş process kill - Windows/Linux uyumlu"""
        try:
            # Önce child process'leri öldür
            try:
                children = process.children(recursive=True)
                for child in children:
                    try:
                        if sys.platform == 'win32':
                            # Windows için
                            child.send_signal(signal.CTRL_BREAK_EVENT)
                            child.terminate()
                        else:
                            # Linux/Mac için
                            child.terminate()
                        
                        # 1 saniye bekle
                        child.wait(timeout=1)
                    except (psutil.NoSuchProcess, psutil.TimeoutExpired):
                        # Hala çalışıyorsa kill et
                        try:
                            child.kill()
                        except:
                            pass
                    except:
                        pass
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
            
            print(f"🔪 Process killed: {process.pid}")
            
        except Exception as e:
            print(f"❌ Kill error: {e}")

    def _cleanup_temp_files(self):
        """Geçici dosyaları temizle"""
        patterns = ['*.part', '*.ytdl', '*.temp', '*.f*-*.m4a', '*.f*-*.mp4']
        for p in patterns:
            for f in glob.glob(p):
                try: 
                    os.remove(f)
                except: 
                    pass
    
    # ============== DİNAMİK YÖNETİM FONKSİYONLARI ==============
    
    async def set_max_concurrent(self, new_limit):
        """Maksimum eşzamanlı indirme sayısını dinamik olarak değiştirir"""
        async with self._stats_lock:
            old_limit = self.max_concurrent
            self.max_concurrent = new_limit
            
            current_available = await self.semaphore.get_value()
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