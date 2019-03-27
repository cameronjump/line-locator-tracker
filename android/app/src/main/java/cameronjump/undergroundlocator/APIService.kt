package cameronjump.undergroundlocator

import com.google.gson.annotations.SerializedName
import io.reactivex.Observable
import retrofit2.Retrofit
import retrofit2.adapter.rxjava2.RxJava2CallAdapterFactory
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.GET

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

    data class Data(
        @SerializedName("mode") val mode:String,
        @SerializedName("value") val value:String,
        @SerializedName("unit") val unit:String,
        @SerializedName("extra") val extra:String)
}