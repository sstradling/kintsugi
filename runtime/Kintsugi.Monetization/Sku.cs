namespace Kintsugi.Monetization;

/// <summary>
/// IAP SKU identifiers used across the monetization layer.
/// </summary>
/// <remarks>
/// Per decision D4, two classes of SKU exist:
/// <list type="bullet">
///   <item><b>Ad removal</b> — a single non-consumable that permanently
///   disables interstitials and uncaps hints.</item>
///   <item><b>Filler packs</b> — cosmetic non-consumables that unlock
///   finisher fillers. Independent of the ad-removal SKU; available to
///   all players.</item>
/// </list>
/// Strings are stable identifiers — they must match the SKUs configured
/// in App Store Connect and Google Play Console exactly.
/// </remarks>
public static class Sku
{
    public const string AdRemoval = "com.kintsugi.adremoval";

    public const string FillerPackGoldPlatinum = "com.kintsugi.fillers.goldplatinum";
    public const string FillerPackOrganic = "com.kintsugi.fillers.organic";
    public const string FillerPackExotic = "com.kintsugi.fillers.exotic";
}
