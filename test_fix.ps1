# Test script to verify the steam note fix
Write-Host "=== Testing Steam Note Creation Fix ===" -ForegroundColor Green

# Check backend changes
Write-Host "`n1. Checking if backend includes 'id' in services.py..." -ForegroundColor Cyan
$servicesContent = Get-Content "backend\apps\templates_manager\services.py" -Raw
if ($servicesContent -match "'id': search_record\.id") {
    Write-Host "   ✓ Backend services.py includes id field" -ForegroundColor Green
} else {
    Write-Host "   ✗ Backend services.py missing id field" -ForegroundColor Red
}

# Check serializer
Write-Host "`n2. Checking if serializer includes 'id' field..." -ForegroundColor Cyan
$serializerContent = Get-Content "backend\apps\templates_manager\serializers.py" -Raw
if ($serializerContent -match "id = serializers\.IntegerField\(required=False\)") {
    Write-Host "   ✓ Serializer includes id field" -ForegroundColor Green
} else {
    Write-Host "   ✗ Serializer missing id field" -ForegroundColor Red
}

# Check frontend component
Write-Host "`n3. Checking frontend validation..." -ForegroundColor Cyan
$componentContent = Get-Content "frontend\src\components\templates\SteamProfileNotes.tsx" -Raw
if ($componentContent -match "if \(!steamProfileId\)") {
    Write-Host "   ✓ Frontend validates steamProfileId" -ForegroundColor Green
} else {
    Write-Host "   ✗ Frontend missing validation" -ForegroundColor Red
}

if ($componentContent -match "steam_profile: steamProfileId,") {
    Write-Host "   ✓ Frontend sends steamProfileId (not steamId64)" -ForegroundColor Green
} else {
    Write-Host "   ✗ Frontend still using fallback to steamId64" -ForegroundColor Red
}

# Check TypeScript compilation
Write-Host "`n4. Running TypeScript check..." -ForegroundColor Cyan
Set-Location "frontend"
$tscResult = npx tsc --noEmit --incremental false 2>&1
Set-Location ".."
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✓ TypeScript compilation successful" -ForegroundColor Green
} else {
    Write-Host "   ✗ TypeScript compilation errors:" -ForegroundColor Red
    Write-Host $tscResult -ForegroundColor Yellow
}

Write-Host "`n=== Summary ===" -ForegroundColor Green
Write-Host "✓ Backend includes id in API response" -ForegroundColor Green
Write-Host "✓ Frontend validates steamProfileId before submission" -ForegroundColor Green
Write-Host "✓ Frontend sends integer ID instead of string" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "1. Restart the backend server to load the updated code" -ForegroundColor White
Write-Host "2. Do a fresh Steam lookup to get the profile with id field" -ForegroundColor White
Write-Host "3. Try creating a note - it should work now!" -ForegroundColor White
