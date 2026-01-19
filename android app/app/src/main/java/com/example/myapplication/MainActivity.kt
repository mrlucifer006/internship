package com.example.myapplication

import android.Manifest
import android.app.Activity
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Environment
import android.provider.MediaStore
import android.view.View
import android.webkit.ValueCallback
import android.webkit.WebChromeClient
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.ProgressBar
import android.widget.Toast
import androidx.activity.OnBackPressedCallback
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.core.content.FileProvider
import androidx.lifecycle.lifecycleScope
import io.github.jan.supabase.SupabaseClient
import io.github.jan.supabase.createSupabaseClient
import io.github.jan.supabase.postgrest.Postgrest
import io.github.jan.supabase.postgrest.from
import io.github.jan.supabase.serializer.KotlinXSerializer
import kotlinx.coroutines.launch
import kotlinx.serialization.json.Json
import java.io.File
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView
    private lateinit var progressBar: ProgressBar

    // File Upload Handling
    private var fileUploadCallback: ValueCallback<Array<Uri>>? = null
    private var pendingFileChooserParams: WebChromeClient.FileChooserParams? = null
    private var cameraImageUri: Uri? = null

    private val fileChooserLauncher = registerForActivityResult(ActivityResultContracts.StartActivityForResult()) { result ->
        if (result.resultCode == Activity.RESULT_OK) {
            val data = result.data
            var results: Array<Uri>? = null

            if (data == null || data.data == null) {
                if (cameraImageUri != null) {
                    results = arrayOf(cameraImageUri!!)
                }
            } else {
                 val dataString = data.dataString
                 if (dataString != null) {
                     results = arrayOf(Uri.parse(dataString))
                 }
            }

            fileUploadCallback?.onReceiveValue(results)
        } else {
            fileUploadCallback?.onReceiveValue(null)
        }
        fileUploadCallback = null
        pendingFileChooserParams = null
        cameraImageUri = null
    }

    private val requestPermissionLauncher = registerForActivityResult(ActivityResultContracts.RequestMultiplePermissions()) { permissions ->
        val granted = permissions.entries.all { it.value }
        if (granted) {
            launchFileChooser(pendingFileChooserParams)
        } else {
            Toast.makeText(this, "Permissions denied. Cannot upload images.", Toast.LENGTH_SHORT).show()
            fileUploadCallback?.onReceiveValue(null)
            fileUploadCallback = null
            pendingFileChooserParams = null
        }
    }

    private fun launchFileChooser(params: WebChromeClient.FileChooserParams?) {
        var takePictureIntent: Intent? = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
        if (takePictureIntent?.resolveActivity(packageManager) != null) {
            var photoFile: File? = null
            try {
                photoFile = createImageFile()
            } catch (ex: Exception) {
                android.util.Log.e("WebView", "Image file creation failed", ex)
                takePictureIntent = null
            }

            if (photoFile != null) {
                cameraImageUri = FileProvider.getUriForFile(
                    this,
                    "${packageName}.provider",
                    photoFile
                )
                takePictureIntent?.putExtra(MediaStore.EXTRA_OUTPUT, cameraImageUri)
            } else {
                takePictureIntent = null
            }
        }

        val contentSelectionIntent = params?.createIntent()
        
        val intentArray: Array<Intent?> = if (takePictureIntent != null) {
            arrayOf(takePictureIntent)
        } else {
            arrayOfNulls(0)
        }

        val chooserIntent = Intent(Intent.ACTION_CHOOSER)
        chooserIntent.putExtra(Intent.EXTRA_INTENT, contentSelectionIntent)
        chooserIntent.putExtra(Intent.EXTRA_TITLE, "Image Chooser")
        chooserIntent.putExtra(Intent.EXTRA_INITIAL_INTENTS, intentArray)

        try {
            fileChooserLauncher.launch(chooserIntent)
        } catch (e: Exception) {
            android.util.Log.e("WebView", "Cannot launch file chooser", e)
            fileUploadCallback?.onReceiveValue(null)
            fileUploadCallback = null
        }
    }

    private fun createImageFile(): File {
        val timeStamp = SimpleDateFormat("yyyyMMdd_HHmmss", Locale.US).format(Date())
        val imageFileName = "JPEG_" + timeStamp + "_"
        val storageDir = getExternalFilesDir(Environment.DIRECTORY_PICTURES)
        return File.createTempFile(
            imageFileName,
            ".jpg",
            storageDir
        )
    }

    private val urls = listOf(
        "https://follows-kingston-spring-registry.trycloudflare.com",
        "http://10.0.2.2:5000",
        "http://10.0.2.2:8000",
        "http://10.0.2.2:8080"
    )
    private var currentUrlIndex = 0
    private var isErrorOccurred = false

    private val supabaseUrl = "https://tordrlujtfoechgrywmk.supabase.co"
    private val supabaseKey = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRvcmRybHVqdGZvZWNoZ3J5d21rIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njc2MTEyODYsImV4cCI6MjA4MzE4NzI4Nn0.f3DR_P8JErRFyhRNmGYPDv9_U19WNcUXGraunO_KzUw"

    private val supabase: SupabaseClient by lazy {
        createSupabaseClient(supabaseUrl, supabaseKey) {
            install(Postgrest)
            // Use defaultSerializer property in the latest versions of Supabase-kt
            defaultSerializer = KotlinXSerializer(Json {
                ignoreUnknownKeys = true
                coerceInputValues = true
            })
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        webView = findViewById(R.id.webView)
        progressBar = findViewById(R.id.progressBar)

        setupWebView()
        fetchUrlAndLoad()

        onBackPressedDispatcher.addCallback(this, object : OnBackPressedCallback(true) {
            override fun handleOnBackPressed() {
                if (webView.canGoBack()) {
                    webView.goBack()
                } else {
                    isEnabled = false
                    onBackPressedDispatcher.onBackPressed()
                }
            }
        })
    }

    private fun setupWebView() {
        val webSettings: WebSettings = webView.settings
        webSettings.javaScriptEnabled = true
        webSettings.domStorageEnabled = true
        webSettings.loadWithOverviewMode = true
        webSettings.useWideViewPort = true
        
        webView.webChromeClient = object : WebChromeClient() {
            override fun onShowFileChooser(
                webView: WebView?,
                filePathCallback: ValueCallback<Array<Uri>>?,
                fileChooserParams: FileChooserParams?
            ): Boolean {
                if (fileUploadCallback != null) {
                    fileUploadCallback?.onReceiveValue(null)
                }
                fileUploadCallback = filePathCallback
                pendingFileChooserParams = fileChooserParams
                
                val permissions = mutableListOf<String>()
                permissions.add(Manifest.permission.CAMERA)
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                     permissions.add(Manifest.permission.READ_MEDIA_IMAGES)
                } else {
                     permissions.add(Manifest.permission.READ_EXTERNAL_STORAGE)
                }
                
                val permissionsToRequest = permissions.filter {
                    ContextCompat.checkSelfPermission(this@MainActivity, it) != PackageManager.PERMISSION_GRANTED
                }
                
                if (permissionsToRequest.isEmpty()) {
                    launchFileChooser(fileChooserParams)
                } else {
                    requestPermissionLauncher.launch(permissionsToRequest.toTypedArray())
                }
                return true
            }
        }
        
        webView.webViewClient = object : WebViewClient() {
            override fun onPageFinished(view: WebView?, url: String?) {
                super.onPageFinished(view, url)
                if (!isErrorOccurred) {
                    progressBar.visibility = View.GONE
                    webView.visibility = View.VISIBLE
                }
            }

            override fun onReceivedError(
                view: WebView?,
                request: android.webkit.WebResourceRequest?,
                error: android.webkit.WebResourceError?
            ) {
                super.onReceivedError(view, request, error)
                if (request?.isForMainFrame == true) {
                    isErrorOccurred = true
                    android.util.Log.e("WebView", "Error loading ${request.url}: ${error?.description}")
                    tryNextUrl()
                }
            }
        }
    }

    private fun fetchUrlAndLoad() {
        progressBar.visibility = View.VISIBLE
        
        lifecycleScope.launch {
            try {
                android.util.Log.d("WebView", "Querying Supabase...")
                val table = supabase.from("employee")
                
                val response = table.select {
                    filter {
                        ilike("connection_mode", "server")
                    }
                }
                
                val employees = response.decodeAs<List<Employee>>()
                android.util.Log.d("WebView", "Rows found: ${employees.size}")
                
                if (employees.isEmpty()) {
                    android.util.Log.w("WebView", "No rows found with filter. Checking if ANY rows are visible...")
                    val allRows = table.select().decodeAs<List<Employee>>()
                    android.util.Log.d("WebView", "Total visible rows in table: ${allRows.size}")
                }

                val employee = employees.firstOrNull()
                
                if (employee != null && !employee.public_url.isNullOrEmpty()) {
                    android.util.Log.d("WebView", "URL Found: ${employee.public_url}")
                    isErrorOccurred = false
                    runOnUiThread {
                        webView.loadUrl(employee.public_url!!)
                    }
                } else {
                    android.util.Log.w("WebView", "Fallback triggered: No valid 'server' row.")
                    runOnUiThread { startFallbackChain() }
                }
            } catch (e: Exception) {
                android.util.Log.e("WebView", "Supabase error: ${e.message}", e)
                runOnUiThread {
                    Toast.makeText(this@MainActivity, "Supabase Error: ${e.message}", Toast.LENGTH_SHORT).show()
                    startFallbackChain()
                }
            }
        }
    }

    private fun startFallbackChain() {
        currentUrlIndex = 0
        loadCurrentUrl()
    }

    private fun tryNextUrl() {
        currentUrlIndex++
        if (currentUrlIndex < urls.size) {
            loadCurrentUrl()
        } else {
            runOnUiThread {
                progressBar.visibility = View.GONE
                webView.visibility = View.VISIBLE
                webView.loadData("<html><body><h1>Connection Failed</h1><p>Check your RLS policies and DB values.</p></body></html>", "text/html", "UTF-8")
            }
        }
    }

    private fun loadCurrentUrl() {
        isErrorOccurred = false
        val url = urls[currentUrlIndex]
        android.util.Log.d("WebView", "Loading fallback: $url")
        runOnUiThread {
            webView.loadUrl(url)
        }
    }
}