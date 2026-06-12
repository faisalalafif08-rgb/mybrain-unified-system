# Core Module Configuration
# مكونات النظام الأساسية

from .news_fetcher import NewsFetcher
from .text_generator import TextGenerator
from .fooocus_handler import FooocusHandler
from .avatar_generator import AvatarGenerator
from .video_editor import VideoEditor
from .tts_handler import TTSHandler

__all__ = [
    'NewsFetcher',
    'TextGenerator',
    'FooocusHandler',
    'AvatarGenerator',
    'VideoEditor',
    'TTSHandler'
]
