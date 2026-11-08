package com.gathin.tvhome;

import org.junit.Test;

import java.io.File;
import java.io.FileNotFoundException;
import java.nio.file.Files;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.fail;

public class ThemeProviderPathTest {
    @Test public void resolvesAllowedPathInsideThemeDirectory() throws Exception {
        File root = Files.createTempDirectory("theme-provider").toFile();
        try {
            File resolved = ThemeProvider.safeFile(root, "wallpapers/dusk.jpg");
            assertEquals(new File(root, "wallpapers/dusk.jpg").getCanonicalFile(), resolved);
        } finally {
            root.delete();
        }
    }

    @Test public void rejectsTraversalOutsideThemeDirectory() throws Exception {
        File root = Files.createTempDirectory("theme-provider").toFile();
        try {
            try {
                ThemeProvider.safeFile(root, "../outside.txt");
                fail("path traversal must be rejected");
            } catch (FileNotFoundException expected) {
                // Expected: the resolved target must stay below the canonical theme directory.
            }
        } finally {
            root.delete();
        }
    }
}