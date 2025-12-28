def is_youtube_link_checker(url: str) -> bool:
    import re
    if not isinstance(url, str) or not url.strip():
        return False

    pattern = re.compile(
        r"^(?:https?://)?(?:www\.)?"
        r"(?:youtube\.com|m\.youtube\.com|youtu\.be)/"
        r"(?:"
            r"watch\?v=[A-Za-z0-9_-]{11}"
            r"|shorts/[A-Za-z0-9_-]{11}"
            r"|embed/[A-Za-z0-9_-]{11}"
            r"|v/[A-Za-z0-9_-]{11}"
            r"|[A-Za-z0-9_-]{11}"
        r")"
        r"(?:[?&][^\s]*)?$",
        re.IGNORECASE
    )

    return bool(pattern.match(url.strip()))


from .video_info import VideoInfo
async def get_video_info(url:str) -> VideoInfo:
    import yt_dlp
    import asyncio
    from models.video_info import VideoInfo
    
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,  # Tüm bilgileri çek
        }
    
    def extract_info():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl: # type: ignore
            return ydl.extract_info(url, download=False)
    
    info_dict = await asyncio.to_thread(extract_info)
    
    video_info = VideoInfo(
    url=url,
    title=info_dict.get('title', 'Bilinmeyen'), # type: ignore
    duration=info_dict.get('duration', 0), # type: ignore
    thumbnail_url=info_dict.get('thumbnail', ''), # type: ignore
    channel=info_dict.get('uploader', ''), # type: ignore
    available_qualities=_get_available_qualities(info_dict), # type: ignore
    filesize_approx=info_dict.get('filesize', 0),
    #available_formats= info_dict.get('formats', [])# type: ignore
    )
    return video_info


from typing import List
# Standart YouTube kalite çözünürlükleri (büyükten küçüğe)
STANDARD_RESOLUTIONS = {
    2160:"2160p",
    1440: "1440p",
    1080: "1080p",
    720: "720p",
    480: "480p",
    360: "360p",
    240: "240p",
    144: "144p",
}
def _get_available_qualities(info_dict: dict) -> List[str]:
    """
    Videoda mevcut olan tüm standart çözünürlükleri al
    
    Returns:
        List[str]: ["4K", "1080p", "720p", ...] gibi büyükten küçüğe
    """
    formats = info_dict.get('formats', [])
    available_heights = set()
    
    # Tüm formatlardan height bilgisini topla
    for fmt in formats:
        height = fmt.get('height')
        if height and height in STANDARD_RESOLUTIONS:
            available_heights.add(height)
    
    # Büyükten küçüğe sırala ve isimlere çevir
    result = []
    for height in sorted(STANDARD_RESOLUTIONS.keys(), reverse=True):
        if height in available_heights:
            result.append(STANDARD_RESOLUTIONS[height])
    
    return result
