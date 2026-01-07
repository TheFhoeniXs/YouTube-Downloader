# 🎬 YouTube to PDF Converter 📄

> 🚀 A powerful desktop application that converts YouTube video transcripts into beautiful PDF documents! Built with Python and Flet framework.

<p align="center">
  <img src="src/assets/screenshots/main_ui.png" width="45%" alt="Main UI"/>
  <img src="src/assets/screenshots/settings_ui.png" width="45%" alt="Settings UI"/>
</p>

## ✨ Features

- 🎥 **YouTube Transcript Extraction**: Automatically fetches video transcripts from YouTube
- 📄 **PDF Generation**: Converts transcripts into well-formatted PDF documents
- 📋 **Queue Management**: Process multiple videos in a queue system
- ⚙️ **Settings Panel**: Configure API key and download directory
- 🌙 **Dark Theme UI**: Modern and clean dark-themed interface
- 📊 **Progress Tracking**: Real-time progress updates for each conversion task
- ⚡ **Async Operations**: Non-blocking video processing with async/await
- 🎯 **URL Validation**: Smart YouTube URL detection and validation
- ❌ **Task Cancellation**: Cancel individual tasks anytime

## 📋 Requirements

- 🐍 Python 3.10+
- 🌐 Active internet connection
- 🔑 TranscriptAPI key (for fetching YouTube transcripts)

## 📦 Installation

### 1️⃣ **Clone the repository**
```bash
git clone https://github.com/TheFhoeniXs/YouTube-to-PDF-Converter.git
cd youtube-pdf-converter
```

### 2️⃣ **Install dependencies**
```bash
pip install -r requirements.txt
```

### 📚 Required Libraries

```txt
flet          # 🎨 Modern UI framework
aiohttp       # 🌐 Async HTTP client
reportlab     # 📄 PDF generation
```

## 🚀 Quick Start

### 1️⃣ **Start the application**
```bash
python main.py
```

### 2️⃣ **Configure Settings** ⚙️
   - Click the settings icon (⚙️) in the top-right corner
   - 🔑 Enter your TranscriptAPI key
   - 📁 Select download directory for PDF files
   - 💾 Click "Save Settings"

### 3️⃣ **Convert YouTube Videos** 🎬
   - 📋 Paste a YouTube URL into the input field
   - ✅ Press Enter or click outside the field to validate
   - 🎯 Click "Convert to PDF" to start processing
   - 📊 Monitor progress in the queue panel

## 📁 Project Structure

```
src/
├── 🎯 main.py                          # Main application entry point
├── 📦 services/
│   ├── 🎥 transcript.py                # YouTube transcript fetching service
│   ├── 📄 pdf_generate.py              # PDF generation service
│   ├── ⚙️ settings_manager.py          # Settings management service
│   └── 💾 settings/
│       └── settings.json               # User settings storage
├── 📖 README.md                        # Project documentation
└── 📋 requirements.txt                 # Python dependencies
```

## 🔧 Configuration

Settings are stored in `services/settings/settings.json`:

```json
{
    "api_key": "your-api-key-here",           // 🔑 Your TranscriptAPI key
    "download_path": "/path/to/folder",       // 📁 PDF save location
    "auto_save": false                        // 💾 Auto-save feature
}
```

## 🎨 Features in Detail

### 📋 Video Queue System
- ➕ Add multiple YouTube URLs
- 🔄 Automatic sequential processing
- ❌ Cancel tasks individually
- 📊 Real-time progress tracking
- 🎯 Smart task management

### ⚙️ Settings Management
- 💾 Persistent configuration storage
- ✅ API key validation
- 📁 Custom download directory
- 🔄 Auto-save functionality (planned)
- 💬 Visual feedback on save

### 📄 PDF Generation
- ✨ Clean formatting
- 📝 Video title as filename
- ⏱️ Timestamp-based text organization
- 📊 Progress callbacks
- 🎨 Professional layout

## 🔗 Supported YouTube URL Formats

✅ `https://www.youtube.com/watch?v=VIDEO_ID`
✅ `https://youtu.be/VIDEO_ID`
✅ `https://www.youtube.com/embed/VIDEO_ID`
✅ `https://www.youtube.com/v/VIDEO_ID`

## 🔑 API Configuration

This application uses **TranscriptAPI** for fetching YouTube transcripts. 

### 📝 Steps to get your API key:

1. 🌐 Sign up at [TranscriptAPI](https://transcriptapi.com)
2. 🔑 Get your API key from dashboard
3. ⚙️ Enter the key in application settings
4. ✅ Start converting videos!

## 🐛 Error Handling

The application intelligently handles:

- ❌ Invalid YouTube URLs
- 🌐 Network connection errors
- 🔑 API authentication failures
- ⚙️ Missing settings configuration
- 🛑 Task cancellation
- 📁 Invalid download paths
- ⏱️ Request timeouts

## 💡 Usage Tips

💡 **Pro Tip 1**: Configure your settings before adding videos to the queue!

💡 **Pro Tip 2**: You can add multiple videos at once and they'll process sequentially

💡 **Pro Tip 3**: Use the cancel button (❌) to remove tasks you don't need

💡 **Pro Tip 4**: The app validates URLs automatically - just paste and go!

## 📝 Code Comments Convention

The codebase uses a color-coded comment system:
- 🔴 `#!` **Red comments** - Critical functions and main operations
- 🔵 `#?` **Blue comments** - Explanatory comments and details

## 🎯 Workflow Example

```
1. 📋 Paste YouTube URL → 
2. ✅ URL Validated → 
3. ➕ Added to Queue → 
4. 🎯 Click "Convert to PDF" → 
5. 📊 Processing... → 
6. 📄 PDF Generated → 
7. 💾 Saved to Your Folder → 
8. ✨ Done!
```

## 🔮 Future Enhancements

- [ ] 💾 Auto-save functionality
- [ ] 🌍 Multiple language support
- [ ] 📜 Export history tracking
- [ ] 🔤 Subtitle language selection
- [ ] 🎬 Video thumbnail in PDF
- [ ] 🐞 bug fixes and UI improvements


## 🤝 Contributing

🎉 Contributions are welcome! Feel free to:

- 🐛 Report bugs
- 💡 Suggest new features
- 🔧 Submit pull requests
- 📖 Improve documentation
- ⭐ Star the project

## 📄 License

📜 This project is open source and available under the [MIT License](LICENSE).

## 👨‍💻 Developer Notes

### 🔑 Key Classes

- 📋 **VideoQueue**: Manages task queue and sequential processing
- 🎬 **VideoTask**: Represents individual conversion tasks
- ⚙️ **SettingsPanel**: UI for application configuration
- 💾 **SettingsManager**: Handles settings persistence

### 🏗️ Architecture

The application follows a service-oriented architecture:
- 🎯 Separation of concerns (UI, Services, Data)
- ⚡ Async/await for non-blocking operations
- 🔄 Event-driven UI updates
- 💾 Persistent settings management
- 🎨 Modern Flet framework

### 🛠️ Tech Stack

- 🐍 **Python 3.10+**: Core language
- 🎨 **Flet**: Cross-platform UI framework
- 🌐 **aiohttp**: Async HTTP requests
- 📄 **ReportLab**: PDF generation
- 💾 **JSON**: Settings storage

## 📊 Performance

- ⚡ Fast async processing
- 💪 Multiple videos in queue
- 📊 Real-time progress updates
- 🔄 Non-blocking UI
- 💾 Lightweight footprint

## 🎓 Learning Resources

- 📖 [Flet Documentation](https://flet.dev)
- 🌐 [aiohttp Documentation](https://docs.aiohttp.org)
- 📄 [ReportLab Documentation](https://www.reportlab.com/docs/)
- 🔑 [TranscriptAPI Docs](https://transcriptapi.com/docs)

## 📞 Support & Community

💬 **Need Help?**
- 🐛 Found a bug? Open an issue on GitHub
- 💡 Have a suggestion? Start a discussion
- 📧 Need support? Contact us
- ⭐ Like the project? Give it a star!

## 🌟 Showcase

```
╔══════════════════════════════════════╗
║   🎬 YouTube to PDF Converter 📄    ║
╠══════════════════════════════════════╣
║  ✨ Fast • Simple • Beautiful ✨    ║
╚══════════════════════════════════════╝
```

## 🎉 Credits

Made with ❤️ by developers who love automation

---

⚠️ **Important Note**: This application requires a valid TranscriptAPI subscription to function. Make sure to configure your API key before using the application.

🚀 **Ready to start?** Clone the repo and start converting! 

⭐ **Don't forget to star the project if you find it useful!** ⭐

---

<div align="center">

### 🎯 Happy Converting! 📄✨

Made with 💙 and lots of ☕

</div>