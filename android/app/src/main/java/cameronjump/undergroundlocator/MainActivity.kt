package cameronjump.undergroundlocator

import android.net.Uri
import android.support.v7.app.AppCompatActivity
import android.os.Bundle
import android.os.Handler
import android.text.Editable
import android.text.TextWatcher
import android.util.Log
import android.webkit.URLUtil
import android.widget.Toast
import com.google.gson.annotations.SerializedName
import io.reactivex.Observable
import io.reactivex.android.schedulers.AndroidSchedulers
import io.reactivex.schedulers.Schedulers
import kotlinx.android.synthetic.main.activity_main.*
import retrofit2.Retrofit
import retrofit2.adapter.rxjava2.RxJava2CallAdapterFactory
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.GET
import java.util.*

class MainActivity : AppCompatActivity() {

    private val TAG = "MainDebug"

    lateinit var service: APIService
    var run = false
    var concurrentFails = 0

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        ip_edit.append(getString(R.string.default_ip))
        service = APIService.create("http://"+ip_edit.text.toString()+":5000")

        ip_edit.addTextChangedListener(object: TextWatcher {
            override fun afterTextChanged(s: Editable?) {
                val ip = "http://"+ip_edit.text.toString()+":5000"
                when (URLUtil.isValidUrl(ip) && ip_edit.text.toString() == "") {
                    true -> {
                        run = true
                        concurrentFails = 0
                        service = APIService.create(ip)
                        Log.d(TAG, ip)}
                    }
            }
            override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) {
            }

            override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) {
            }
        })

        callAsynchronousTask()
    }

    private fun callAsynchronousTask() {
        val handler = Handler()
        val timer = Timer()
        val doAsynchronousTask = object : TimerTask() {
            override fun run() {
                handler.post {
                    try {
                        retrieveValue()
                    } catch (e: Exception) {
                        Log.d(TAG, e.toString())
                    }
                }
            }
        }
        timer.schedule(doAsynchronousTask, 0, 250) //250ms
    }

    private fun retrieveValue() {
        if(run) {
            val observable = service.getValue()
            observable.subscribeOn(Schedulers.io())
                .observeOn(AndroidSchedulers.mainThread())
                .subscribe(
                    { result -> Log.d(TAG, result.toString())
                        concurrentFails = 0
                        mode_text.text = result.mode
                        value_text.text = result.value + result.unit
                        extra_text.text = result.extra
                        status_text.background = getDrawable(R.drawable.status_on)
                        status_text.text = "Connected"
                    },
                    { error -> Log.d(TAG, "Error" + error.toString())
                        concurrentFails += 1
                        if(concurrentFails == 5) {
                            Toast.makeText(this, error.toString(), Toast.LENGTH_LONG).show()
                            mode_text.text = ""
                            value_text.text = ""
                            extra_text.text = ""
                            status_text.background = getDrawable(R.drawable.status_off)
                            status_text.text = "Disconnected"
                        }
                    }
                )
        }
    }

    override fun onResume() {
        super.onResume()
        run = true
    }

    override fun onRestart() {
        super.onRestart()
        run = true
    }

    override fun onPause() {
        super.onPause()
        run = false
    }

    override fun onDestroy() {
        super.onDestroy()
        run = false
    }

}
