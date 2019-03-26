package cameronjump.undergroundlocator

import android.net.Uri
import android.support.v7.app.AppCompatActivity
import android.os.Bundle
import android.text.Editable
import android.text.TextWatcher
import android.util.Log
import android.webkit.URLUtil
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
import kotlin.concurrent.schedule

class MainActivity : AppCompatActivity() {

    private val TAG = "MainDebug"

    lateinit var service: APIService

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        service = APIService.create("http://phoney")

        ip.addTextChangedListener(object: TextWatcher {
            override fun afterTextChanged(s: Editable?) {
                val ip = ip.text.toString()
                when (URLUtil.isValidUrl(ip)) {
                    true -> service = APIService.create(ip)
                }
            }

            override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) {
            }

            override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) {
            }
        })

        Timer().schedule(100){
            retrieveValue()
        }
    }

    private fun retrieveValue() {
        if(service != null) {
            val observable = service.getValue()
            observable.subscribeOn(Schedulers.io())
                .observeOn(AndroidSchedulers.mainThread())
                .subscribe(
                    { result -> Log.d(TAG, result.toString())
                        text.text = result.title
                        contents.text = result.value
                    },
                    { error ->
                        Log.d(TAG, "Error" + error.toString())
                    }
                )


        }
    }

    interface APIService {

        @GET("/api")
        fun getValue() : Observable<Data>

        companion object {
            fun create(ip: String): APIService {

                val retrofit = Retrofit.Builder()
                    .addCallAdapterFactory(RxJava2CallAdapterFactory.create())
                    .addConverterFactory(GsonConverterFactory.create())
                    .baseUrl(ip)
                    .build()

                return retrofit.create(APIService::class.java)
            }
        }
    }

    data class Data(@SerializedName("title") val title:String, @SerializedName("value") val value:String)

}
