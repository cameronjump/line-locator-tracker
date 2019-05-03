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

        service = APIService.create("http://10.0.0.1:5000")

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
                        val values = result.split(',')
                        val current_mode = values[0]
                        val current_value = values[1]
                        val value0 = values[2]
                        val value1 = values[3]
                        val value_ref = values[4]
                        val message = values[5]
                        val gain_value = values[6]
                        val calibration_distance = values[7]
                        val calibration_value = values[8]
                        mode_text.text = current_mode
                        value_text.text = "%s%s".format(current_value, "ft")
                        extra_text.text = "%s\n%s\n%s".format(value0, value1, value_ref)
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
