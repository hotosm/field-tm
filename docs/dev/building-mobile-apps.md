# Building Mobile App Wrappers

It's possible to build app 'wrappers' around the Field-TM web app,
that can be published to Android or iOS app stores.

These 'apps' simply wrap the website in a web view. However, the
operating system grants them additional privileges that a standard
web app does not have (for instance, high memory usage).

Note that Android publishing cost a lifetime fee of $25, while iOS
publishing is $99 annually.

## Android

### Android PWABuilder

The simplest approach is to use [pwabuilder.com](pwabuilder.com) to do this.

Point the website to your PWA, and it will package it up for you, providing
a final APK/AAB you can publish.

It's also possible to use the tool
[Bubblewrap](https://github.com/GoogleChromeLabs/bubblewrap) directly
(used by PWABuilder) to generate the APK yourself.

### Android Manually

It's possible to build an Android project from scratch, then simply
update `MainActivity.kt` to be as follows:

```kotlin
import android.os.Bundle
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        val webView = findViewById<WebView>(R.id.webView)
        webView.webViewClient = WebViewClient()

        // Load Web App
        webView.loadUrl("https://mapper.fmtm.hotosm.org")
    }
}
```

You will also need `activity_main.xml` for the layout:

```xml
<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:tools="http://schemas.android.com/tools"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    tools:context=".MainActivity">

    <WebView
        android:id="@+id/webView"
        android:layout_width="match_parent"
        android:layout_height="match_parent" />

</LinearLayout>
```

## iOS

Unless we have a Mac with XCode installed to build with, we need a workaround
to run an emulated MacOS machine via a container.

Luckily [this repo](https://github.com/sickcodes/Docker-OSX?tab=readme-ov-file#initial-setup)
has some great pre-built containers that do just this.

### iOS PWABuilder

As with Android above, simply visit [pwabuilder.com](pwabuilder.com) to do this.

Point the website to your PWA, and it will package it up for you, providing
an XCode project that can be worked on.

Follow the
[instructions on the website](https://docs.pwabuilder.com/#/builder/app-store?id=building-your-app)
to build and publish the app to iOS.

### iOS Manually

WKWebview can be used to wrap the web app:

```swift
import UIKit
import WebKit

class ViewController: UIViewController {
    var webView: WKWebView!
    override func viewDidLoad() {
        super.viewDidLoad()
        // Initialize WebView
        webView = WKWebView(frame: self.view.frame)
        self.view.addSubview(webView)
        // Load Web App
        if let url = URL(string: "https://mapper.fmtm.hotosm.org") {
            let request = URLRequest(url: url)
            webView.load(request)
        }
    }
}
```
