package org.pocketairdisplay.receiver

import android.content.Context
import android.content.ContextWrapper
import android.content.Intent
import android.os.SystemClock
import androidx.test.core.app.ActivityScenario
import androidx.test.core.app.ApplicationProvider
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.Assert.*
import org.junit.Test

/** Run each class in a fresh instrumentation process; server singleton deliberately has no reset API. */
class InitializationRetryTest {
    @Test fun initializationRetriesAfterAnEarlyFailure() {
        val base = ApplicationProvider.getApplicationContext<Context>()
        val failing = object : ContextWrapper(base) {
            override fun getApplicationContext(): Context = this
            override fun getSharedPreferences(name: String, mode: Int): android.content.SharedPreferences {
                throw IllegalStateException("injected settings failure")
            }
        }
        try {
            WormholeServer.init(failing)
            fail("Expected injected failure before initialization completes")
        } catch (expected: IllegalStateException) {
            assertEquals("injected settings failure", expected.message)
        }
        WormholeServer.init(base)
        assertTrue(WormholeServer.identity.serviceName.isNotBlank())
        assertTrue(WormholeServer.displayInfo.value.width > 0)
    }
}

class ApplicationDisplayTest {
    @Test fun applicationContextHasUsableReceiverDisplay() {
        val context = ApplicationProvider.getApplicationContext<Context>()
        // Invoke the real display-acquisition path, not just its aspect-ratio arithmetic.
        val method = WormholeServer::class.java.getDeclaredMethod("queryDisplayInfo", Context::class.java)
        method.isAccessible = true
        val info = method.invoke(WormholeServer, context) as DisplayInfo
        assertTrue(info.width > 0)
        assertTrue(info.height > 0)
        assertTrue(info.refreshRate > 0)
        WormholeServer.init(context)
        assertTrue(WormholeServer.identity.serviceName.isNotBlank())
    }
}

class ActivityStartupTest {
    @Test fun activityStartsAndStopsReceiverWhenBackgroundDisabled() {
        val context = ApplicationProvider.getApplicationContext<Context>()
        val prefs = context.getSharedPreferences("settings", Context.MODE_PRIVATE)
        val old = prefs.getBoolean("run_in_background", true)
        prefs.edit().putBoolean("run_in_background", false).commit()
        try {
            ActivityScenario.launch(MainActivity::class.java).use { scenario ->
                scenario.onActivity { assertTrue(WormholeServer.displayInfo.value.width > 0) }
                await { WormholeService.isRunning && WormholeServer.isServerRunning() }
                scenario.moveToState(androidx.lifecycle.Lifecycle.State.CREATED)
                await { !WormholeService.isRunning && !WormholeServer.isServerRunning() }
                scenario.moveToState(androidx.lifecycle.Lifecycle.State.RESUMED)
                await { WormholeService.isRunning && WormholeServer.isServerRunning() }
            }
            await { !WormholeService.isRunning }
        } finally {
            context.stopService(Intent(context, WormholeService::class.java))
            prefs.edit().putBoolean("run_in_background", old).commit()
        }
    }
}

class ServiceStartupTest {
    @Test fun serviceFirstStartsWithApplicationContextAndStopsCleanly() {
        val instrumentation = InstrumentationRegistry.getInstrumentation()
        val context = ApplicationProvider.getApplicationContext<Context>()
        val identityPrefs = context.getSharedPreferences("identity", Context.MODE_PRIVATE)
        val previousName = identityPrefs.getString("service_name", null)
        // Exactly 50 standard UTF-8 bytes, but 74 JNI modified UTF-8 bytes.
        // Real service startup must cross JNI and native DNS validation successfully.
        val unicodeName = "😀".repeat(12) + "xx"
        assertEquals(50, unicodeName.toByteArray(Charsets.UTF_8).size)
        assertEquals(unicodeName, WormholeIdentity.sanitizeServiceName(unicodeName))
        identityPrefs.edit().putString("service_name", unicodeName).commit()
        // Test-only exemption; never granted by the app, no overlay/full-screen permission.
        instrumentation.uiAutomation.adoptShellPermissionIdentity("android.permission.START_FOREGROUND_SERVICES_FROM_BACKGROUND")
        try {
            WormholeService.start(context)
            await { WormholeService.isRunning && WormholeServer.isServerRunning() }
            assertTrue(WormholeServer.displayInfo.value.width > 0)
            assertEquals(unicodeName, WormholeServer.identity.serviceName)
            WormholeService.stop(context)
            await { !WormholeService.isRunning && !WormholeServer.isServerRunning() }
        } finally {
            context.stopService(Intent(context, WormholeService::class.java))
            identityPrefs.edit().putString("service_name", previousName).commit()
            instrumentation.uiAutomation.dropShellPermissionIdentity()
        }
    }
}

class PendingStartTest {
    @Test fun duplicateQueuedStartsRetainOneCancellableLease() {
        WormholeServer.init(ApplicationProvider.getApplicationContext<Context>())
        val executorField = WormholeServer::class.java.getDeclaredField("serverExecutor").apply { isAccessible = true }
        val executor = executorField.get(WormholeServer) as java.util.concurrent.ExecutorService
        val entered = java.util.concurrent.CountDownLatch(1)
        val release = java.util.concurrent.CountDownLatch(1)
        executor.execute { entered.countDown(); check(release.await(10, java.util.concurrent.TimeUnit.SECONDS)) }
        assertTrue(entered.await(5, java.util.concurrent.TimeUnit.SECONDS))
        val field = WormholeServer::class.java.getDeclaredField("lease").apply { isAccessible = true }
        var first: ServerLifecycle.Lease? = null
        try {
            WormholeServer.startServer()
            first = field.get(WormholeServer) as ServerLifecycle.Lease
            WormholeServer.startServer()
            assertSame("Duplicate startup overwrote the only cancellable lease", first, field.get(WormholeServer))
            WormholeServer.stopServer()
            assertTrue(first.cancelled.get())
        } finally {
            // Clean both leases even when running this test against the old faulty source.
            first?.cancelled?.set(true)
            WormholeServer.stopServer()
            release.countDown()
            executor.submit {}.get(10, java.util.concurrent.TimeUnit.SECONDS)
        }
        assertFalse(WormholeServer.isServerRunning())
    }
}

class SessionTeardownTest {
    @Test fun explicitStopRecordsMirroringOnce() {
        val context = ApplicationProvider.getApplicationContext<Context>()
        WormholeServer.init(context)
        val prefs = context.getSharedPreferences("connection_history", Context.MODE_PRIVATE)
        val previous = prefs.getString("recent_connections", null)
        fun set(name: String, value: Any) {
            WormholeServer::class.java.getDeclaredField(name).apply { isAccessible = true }.set(WormholeServer, value)
        }
        val name = "test-explicit-stop-" + SystemClock.elapsedRealtime()
        try {
            set("sessionStartTime", System.currentTimeMillis() - 5_000L)
            set("sessionClientName", name)
            set("sessionResolution", "1440 × 2160")
            set("sessionCodec", "H.264")
            WormholeServer.stopServer()
            WormholeServer.stopServer()
            val entries = WormholeServer.history.getRecent().filter { it.clientName == name }
            assertEquals(1, entries.size)
            assertEquals("1440 × 2160", entries.single().resolution)
            assertEquals("H.264", entries.single().codec)
        } finally {
            prefs.edit().putString("recent_connections", previous).commit()
        }
    }
}

private fun await(condition: () -> Boolean) {
    val deadline = SystemClock.elapsedRealtime() + 10_000
    while (!condition() && SystemClock.elapsedRealtime() < deadline) SystemClock.sleep(50)
    assertTrue("Timed out waiting for receiver lifecycle", condition())
}
