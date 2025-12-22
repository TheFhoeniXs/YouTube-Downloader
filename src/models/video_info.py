from dataclasses import dataclass, field
from typing import List

@dataclass
class VideoInfo:
    """YouTube video bilgileri"""
    
    # Temel bilgiler
    url: str                          # Video URL'i
    #video_id: str                     # Video ID (örn: "dQw4w9WgXcQ")
    title: str                        # Video başlığı
    
    # Detay bilgiler
    duration: int = 0                 # Süre (saniye)
    thumbnail_url: str = ""           # Thumbnail URL'i
    #description: str = ""             # Video açıklaması
    
    # Kanal bilgileri
    channel: str = ""                 # Kanal adı
    #channel_id: str = ""              # Kanal ID
    #channel_url: str = ""             # Kanal URL'i
    
    # # İstatistikler
    # view_count: int = 0               # İzlenme sayısı
    # like_count: int = 0               # Beğeni sayısı
    # upload_date: str = ""             # Yüklenme tarihi (YYYYMMDD)
    
    # Format bilgileri
    #available_formats: List[Dict] = field(default_factory=list)  # Mevcut formatlar
    available_qualities: List[str] = field(default_factory=list) # Mevcut kaliteler
    filesize_approx: int = 0          # Yaklaşık dosya boyutu (bytes)
    
    # Computed properties (hesaplanan)
    @property
    def duration_formatted(self) -> str:
        """Süreyi formatla (HH:MM:SS)"""
        if self.duration == 0:
            return "00:00"
        
        hours = self.duration // 3600
        minutes = (self.duration % 3600) // 60
        seconds = self.duration % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"
    
    @property
    def filesize_formatted(self) -> str:
        """Dosya boyutunu formatla"""
        if self.filesize_approx == 0:
            return "Bilinmiyor"
        
        # Bytes to MB/GB
        mb = self.filesize_approx / (1024 * 1024)
        if mb >= 1024:
            gb = mb / 1024
            return f"{gb:.2f} GB"
        return f"{mb:.2f} MB"
    
    @property
    def short_title(self, max_length: int = 50) -> str:
        """Kısa başlık (uzunsa kes)"""
        if len(self.title) <= max_length:
            return self.title
        return self.title[:max_length] + "..."

