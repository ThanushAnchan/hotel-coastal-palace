Add-Type -AssemblyName System.Drawing

$srcDir = "C:\Users\LENOVO\.gemini\antigravity-ide\brain\aa6b9f17-dc31-45e9-ae1c-90e681538e2d\.user_uploaded"
$dstDir = "C:\Users\LENOVO\.gemini\antigravity-ide\scratch\hotel-coastal-palace\static\images"

function Crop-Image($srcPath, $rect, $dstPath) {
    $bmp = [System.Drawing.Bitmap]::FromFile($srcPath)
    $cropped = new-object System.Drawing.Bitmap([int]$rect.Width, [int]$rect.Height)
    $g = [System.Drawing.Graphics]::FromImage($cropped)
    $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
    $g.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
    $dstRect = new-object System.Drawing.Rectangle(0, 0, [int]$rect.Width, [int]$rect.Height)
    $g.DrawImage($bmp, $dstRect, $rect, [System.Drawing.GraphicsUnit]::Pixel)
    $g.Dispose()
    $bmp.Dispose()
    
    $format = [System.Drawing.Imaging.ImageFormat]::Jpeg
    if ($dstPath.EndsWith(".png")) {
        $format = [System.Drawing.Imaging.ImageFormat]::Png
    }
    $cropped.Save($dstPath, $format)
    $cropped.Dispose()
    Write-Host "Saved: $dstPath"
}

# 1. Hotel Exterior
Copy-Item "$srcDir\media_1790680533813.jpg" "$dstDir\hotel\hotel_exterior.jpg" -Force
Write-Host "Copied hotel exterior"

# 2. Reception & Restaurant Interior (media_1790680533827.png: 978x242)
# Panel 1: 0, 0, 320, 242 (Restaurant dining booths)
Crop-Image "$srcDir\media_1790680533827.png" (new-object System.Drawing.Rectangle(4, 4, 316, 234)) "$dstDir\restaurant\restaurant_dining_1.jpg"
# Panel 2: 330, 0, 315, 242 (Front Reception Desk)
Crop-Image "$srcDir\media_1790680533827.png" (new-object System.Drawing.Rectangle(330, 4, 314, 234)) "$dstDir\hotel\reception_lobby.jpg"
# Panel 3: 656, 0, 318, 242 (Restaurant banquet / dining)
Crop-Image "$srcDir\media_1790680533827.png" (new-object System.Drawing.Rectangle(656, 4, 318, 234)) "$dstDir\restaurant\restaurant_dining_2.jpg"

# 3. Rooms (media_1790680533891.png: 977x481)
# Top Row (height 236):
# Col 1: Standard double 1
Crop-Image "$srcDir\media_1790680533891.png" (new-object System.Drawing.Rectangle(4, 4, 318, 232)) "$dstDir\rooms\standard_double_1.jpg"
# Col 2: Deluxe 1
Crop-Image "$srcDir\media_1790680533891.png" (new-object System.Drawing.Rectangle(330, 4, 318, 232)) "$dstDir\rooms\deluxe_1.jpg"
# Col 3: Deluxe 2 (wide)
Crop-Image "$srcDir\media_1790680533891.png" (new-object System.Drawing.Rectangle(656, 4, 317, 232)) "$dstDir\rooms\deluxe_2.jpg"

# Bottom Row (height 236):
# Col 1: Superior Double 1 (suite double bed)
Crop-Image "$srcDir\media_1790680533891.png" (new-object System.Drawing.Rectangle(4, 244, 318, 233)) "$dstDir\rooms\superior_double_1.jpg"
# Col 2: Superior Double 2 (close up bed & chair)
Crop-Image "$srcDir\media_1790680533891.png" (new-object System.Drawing.Rectangle(330, 244, 318, 233)) "$dstDir\rooms\superior_double_2.jpg"
# Col 3: Standard Double 2 (room view with window & TV)
Crop-Image "$srcDir\media_1790680533891.png" (new-object System.Drawing.Rectangle(656, 244, 317, 233)) "$dstDir\rooms\standard_double_2.jpg"

# 4. Food Collage 1 (media_1790680533724.png: 501x758)
# Row 1 Left: Coastal Fish Fry on Banana leaf
Crop-Image "$srcDir\media_1790680533724.png" (new-object System.Drawing.Rectangle(4, 4, 244, 246)) "$dstDir\food\food_fish_fry.jpg"
# Row 1 Right: Kori Sukka / Chicken Sukka
Crop-Image "$srcDir\media_1790680533724.png" (new-object System.Drawing.Rectangle(253, 4, 244, 246)) "$dstDir\food\food_chicken_sukka.jpg"
# Row 2 Left: Coastal Dining Table Platter
Crop-Image "$srcDir\media_1790680533724.png" (new-object System.Drawing.Rectangle(4, 255, 244, 246)) "$dstDir\food\food_restaurant_table.jpg"
# Row 2 Right: Medu Vada with Sambar Chutney
Crop-Image "$srcDir\media_1790680533724.png" (new-object System.Drawing.Rectangle(253, 255, 244, 246)) "$dstDir\food\food_medu_vada.jpg"
# Row 3 Left: Poori Bhaji with Sambar Chutney
Crop-Image "$srcDir\media_1790680533724.png" (new-object System.Drawing.Rectangle(4, 506, 244, 246)) "$dstDir\food\food_poori_bhaji.jpg"
# Row 3 Right: Grilled Club Sandwiches
Crop-Image "$srcDir\media_1790680533724.png" (new-object System.Drawing.Rectangle(253, 506, 244, 246)) "$dstDir\food\food_grilled_sandwich.jpg"

# 5. Food Collage 2 (media_1790680533788.png: 494x773)
# Row 1 Left: Crispy Golden Dosa
Crop-Image "$srcDir\media_1790680533788.png" (new-object System.Drawing.Rectangle(4, 4, 240, 250)) "$dstDir\food\food_crispy_dosa.jpg"
# Row 1 Right: Squid Roast & Seafood Platter
Crop-Image "$srcDir\media_1790680533788.png" (new-object System.Drawing.Rectangle(249, 4, 240, 250)) "$dstDir\food\food_squid_seafood.jpg"
# Row 2 Left: Onion Tomato Uttapam
Crop-Image "$srcDir\media_1790680533788.png" (new-object System.Drawing.Rectangle(4, 260, 240, 250)) "$dstDir\food\food_onion_uttapam.jpg"
# Row 2 Right: Kesari Bath Sheera
Crop-Image "$srcDir\media_1790680533788.png" (new-object System.Drawing.Rectangle(249, 260, 240, 250)) "$dstDir\food\food_kesari_bath.jpg"
# Row 3 Left: Filter Coffee Davara
Crop-Image "$srcDir\media_1790680533788.png" (new-object System.Drawing.Rectangle(4, 516, 240, 250)) "$dstDir\food\food_filter_coffee.jpg"
# Row 3 Right: Gadbad Ice Cream Sundae
Crop-Image "$srcDir\media_1790680533788.png" (new-object System.Drawing.Rectangle(249, 516, 240, 250)) "$dstDir\food\food_gadbad_icecream.jpg"

Write-Host "All assets cropped and saved successfully!"
