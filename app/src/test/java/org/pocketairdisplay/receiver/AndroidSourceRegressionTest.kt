package org.pocketairdisplay.receiver

import java.io.File
import org.junit.Assert.*
import org.junit.Test

/** Structural backstops only; Android behavior is covered by androidTest and device acceptance. */
class AndroidSourceRegressionTest {
    private fun source(name: String): String {
        val root = generateSequence(File(requireNotNull(System.getProperty("user.dir")))) { it.parentFile }
            .first { File(it, "app/src/main/AndroidManifest.xml").exists() }
        return File(root, "app/src/main/$name").readText()
    }
    private fun kotlin(name: String) = source("java/org/pocketairdisplay/receiver/$name.kt")

    @Test fun `non display application context never calls Context display`() {
        assertFalse(kotlin("WormholeServer").contains("context.display"))
    }
    @Test fun `completed initialization rather than assigned context guards retry`() {
        assertFalse(kotlin("WormholeServer").contains("if (::appContext.isInitialized) return"))
    }
    @Test fun `receiver requests notifications but never full screen intent`() {
        val manifest = source("AndroidManifest.xml")
        assertTrue(manifest.contains("android.permission.POST_NOTIFICATIONS"))
        assertFalse(manifest.contains("android.permission.USE_FULL_SCREEN_INTENT"))
        assertFalse(kotlin("WormholeService").contains("setFullScreenIntent"))
        assertTrue(kotlin("MainActivity").contains("ActivityResultContracts.RequestPermission()"))
    }
    @Test fun `background off stops at onStop not only onDestroy`() {
        val activity = kotlin("MainActivity")
        assertTrue(activity.contains("override fun onStop()"))
        val stop = activity.substringAfter("override fun onStop()").substringBefore("override fun")
        assertTrue(stop.contains("!WormholeServer.runInBackground"))
        assertTrue(stop.contains("WormholeService.stop(this)"))
    }
    @Test fun `pending receiver lease prevents duplicate queued starts`() {
        val start = kotlin("WormholeServer").substringAfter("fun startServer()").substringBefore("fun stopServer()")
        assertTrue(start.contains("if (lease != null) return"))
    }
    @Test fun `stop records history before streaming state is cleared`() {
        val stop = kotlin("WormholeServer").substringAfter("fun stopServer()").substringBefore("fun restartServer()")
        assertTrue(stop.indexOf("recordSessionEnd()") in 0 until stop.indexOf("_isMirroring.value = false"))
    }
}
