package org.pocketairdisplay.receiver

import org.junit.Assert.assertEquals
import org.junit.Test

class WormholeIdentityTest {
    @Test fun `UTF8 name fits RAOP prefix without splitting code points`() {
        assertEquals("é".repeat(25), WormholeIdentity.sanitizeServiceName("é".repeat(26)))
        assertEquals("😀".repeat(12), WormholeIdentity.sanitizeServiceName("😀".repeat(13)))
        assertEquals("a".repeat(48) + "é", WormholeIdentity.sanitizeServiceName("a".repeat(48) + "éz"))
        assertEquals("a".repeat(49), WormholeIdentity.sanitizeServiceName("a".repeat(49) + "😀"))
        assertEquals(63, ("0123456789AB@" + WormholeIdentity.sanitizeServiceName("a".repeat(51))).toByteArray(Charsets.UTF_8).size)
    }


    @Test
    fun `sanitizeServiceName returns default name for null blank or default strings`() {
        assertEquals(WormholeIdentity.DEFAULT_SERVICE_NAME, WormholeIdentity.sanitizeServiceName(null))
        assertEquals(WormholeIdentity.DEFAULT_SERVICE_NAME, WormholeIdentity.sanitizeServiceName(""))
        assertEquals(WormholeIdentity.DEFAULT_SERVICE_NAME, WormholeIdentity.sanitizeServiceName("   "))
        assertEquals(WormholeIdentity.DEFAULT_SERVICE_NAME, WormholeIdentity.sanitizeServiceName("WD Display"))
        assertEquals(WormholeIdentity.DEFAULT_SERVICE_NAME, WormholeIdentity.sanitizeServiceName("  WD Display  "))
    }

    @Test
    fun `sanitizeServiceName trims custom names and limits length`() {
        assertEquals("Living Room Display", WormholeIdentity.sanitizeServiceName("  Living Room Display  "))
        val longName = "A".repeat(80)
        assertEquals("A".repeat(50), WormholeIdentity.sanitizeServiceName(longName))
    }
}
