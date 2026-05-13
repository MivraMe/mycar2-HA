# MyCar2 — Home Assistant Integration

Intégration Home Assistant pour le tracker OBD-II **MyCar2** (Automobility).  
Contrôlez et surveillez votre véhicule en temps réel depuis HA.

---

## Fonctionnalités

- **Temps réel** via SignalR (SSE) — les changements d'état apparaissent instantanément
- **Polling REST** toutes les 30 secondes en fallback
- **Synchronisation keyfob** automatique toutes les 5 minutes
- **Démarrage / arrêt distant**, verrouillage, coffre, panic, mode voiturier
- **GPS** avec altitude, cap et vitesse
- **Batterie** en volts, température habitacle, force du signal
- **Multi-véhicules** — une entrée de configuration par véhicule

---

## Installation via HACS

1. Dans HACS, ouvrez **Intégrations** → menu ⋮ → **Dépôts personnalisés**
2. Ajoutez l'URL du dépôt et choisissez la catégorie **Intégration**
3. Recherchez **MyCar2** et cliquez **Télécharger**
4. Redémarrez Home Assistant

### Installation manuelle

Copiez le dossier `custom_components/mycar2/` dans votre répertoire `config/custom_components/`, puis redémarrez.

---

## Configuration

1. Allez dans **Paramètres → Appareils et services → Ajouter une intégration**
2. Recherchez **MyCar2**
3. Entrez votre **courriel** et **mot de passe** MyCar2
4. Si vous avez plusieurs véhicules, sélectionnez celui à connecter
5. L'appareil et toutes ses entités apparaissent immédiatement

> Les identifiants sont stockés dans HA de façon chiffrée. Ne les entrez jamais dans un fichier de configuration YAML.

---

## Entités

### Verrou

| Entité | Description |
|---|---|
| `lock.{nom}_portes` | Verrouillage / déverrouillage des portes |

**Actions disponibles :** `lock.lock`, `lock.unlock`

```yaml
# Exemple d'automatisation — verrouiller en quittant
automation:
  trigger:
    - platform: state
      entity_id: person.vous
      to: not_home
  action:
    - action: lock.lock
      target:
        entity_id: lock.ma_voiture_portes
```

---

### Capteurs binaires

| Entité | Classe | Description |
|---|---|---|
| `binary_sensor.{nom}_moteur` | `running` | Moteur allumé (démarrage distant actif) |
| `binary_sensor.{nom}_contact` | `power` | Contact / allumage |
| `binary_sensor.{nom}_coffre` | `opening` | Coffre ouvert |
| `binary_sensor.{nom}_capot` | `opening` | Capot ouvert |
| `binary_sensor.{nom}_portes` | `door` | Au moins une porte ouverte |
| `binary_sensor.{nom}_hors_ligne` | `connectivity` | Appareil hors ligne |

---

### Capteurs

| Entité | Unité | Description |
|---|---|---|
| `sensor.{nom}_batterie` | V | Tension de la batterie du véhicule |
| `sensor.{nom}_vitesse_gps` | km/h | Vitesse GPS instantanée |
| `sensor.{nom}_signal` | dBm | Force du signal cellulaire (RSSI) |
| `sensor.{nom}_temperature_habitacle` | °C | Température intérieure |
| `sensor.{nom}_version_firmware` | — | Version du firmware du module *(désactivé par défaut)* |

---

### Boutons

| Entité | CarCommand | Description |
|---|---|---|
| `button.{nom}_demarrage_distant` | 3 | Démarrage à distance |
| `button.{nom}_arret_distant` | 4 | Arrêt à distance |
| `button.{nom}_prolonger_duree` | 5 | Prolonger le démarrage distant |
| `button.{nom}_ouvrir_coffre` | 2 | Déverrouiller le coffre |
| `button.{nom}_panic_on` | 6 | Activer l'alarme panique |
| `button.{nom}_panic_off` | 7 | Désactiver l'alarme panique |
| `button.{nom}_mode_voiturier` | 20 | Basculer le mode voiturier |
| `button.{nom}_synchroniser` | 21 | Forcer une synchro d'état *(désactivé par défaut)* |

> Les boutons **Démarrage**, **Arrêt** et **Ouvrir coffre** envoient automatiquement une commande de réveil si l'appareil est hors ligne avant d'exécuter l'action.

```yaml
# Exemple — démarrer la voiture 30 min avant de partir le matin
automation:
  trigger:
    - platform: time
      at: "07:30:00"
  condition:
    - condition: state
      entity_id: binary_sensor.ma_voiture_moteur
      state: "off"
  action:
    - action: button.press
      target:
        entity_id: button.ma_voiture_demarrage_distant
```

---

### Traceur GPS

| Entité | Description |
|---|---|
| `device_tracker.{nom}_position` | Position GPS du véhicule |

L'entité retourne l'état `home` / `not_home` ou le nom d'une **zone HA** si le véhicule s'y trouve.

**Attributs supplémentaires :**

| Attribut | Description |
|---|---|
| `altitude` | Altitude en mètres |
| `heading` | Cap en degrés (0–360) |
| `speed` | Vitesse en km/h |

```yaml
# Exemple — notification quand la voiture arrive à la maison
automation:
  trigger:
    - platform: state
      entity_id: device_tracker.ma_voiture_position
      to: home
  action:
    - action: notify.mobile_app
      data:
        message: "La voiture est arrivée !"
```

---

## Exposer les entités

### Google Assistant / Alexa

1. **Paramètres → Appareils et services → Google Assistant** (ou Alexa)
2. Sélectionnez les entités à exposer  
3. Le verrou (`lock`) et le traceur (`device_tracker`) sont les plus utiles

> Pour des raisons de sécurité, **ne pas exposer** les boutons de démarrage distant aux assistants vocaux sans protection par code PIN.

### Dashboard Lovelace

Carte minimale pour le contrôle du véhicule :

```yaml
type: vertical-stack
cards:
  - type: entity
    entity: lock.ma_voiture_portes
    name: Verrouillage

  - type: glance
    entities:
      - entity: binary_sensor.ma_voiture_moteur
        name: Moteur
      - entity: binary_sensor.ma_voiture_contact
        name: Contact
      - entity: binary_sensor.ma_voiture_coffre
        name: Coffre
      - entity: binary_sensor.ma_voiture_capot
        name: Capot
      - entity: sensor.ma_voiture_batterie
        name: Batterie
      - entity: sensor.ma_voiture_signal
        name: Signal

  - type: map
    entities:
      - entity: device_tracker.ma_voiture_position
    hours_to_show: 1

  - type: horizontal-stack
    cards:
      - type: button
        entity: button.ma_voiture_demarrage_distant
        name: Démarrer
        icon: mdi:car-key
      - type: button
        entity: button.ma_voiture_arret_distant
        name: Arrêter
        icon: mdi:car-off
      - type: button
        entity: button.ma_voiture_ouvrir_coffre
        name: Coffre
        icon: mdi:car-back
```

---

## Comportement technique

| Mécanisme | Détail |
|---|---|
| **Auth** | AWS Cognito `USER_PASSWORD_AUTH` — token rafraîchi automatiquement toutes les 55 min |
| **Temps réel** | SignalR sur SSE — reconnexion automatique avec recul de 15 s |
| **Fallback** | Polling REST `GetLastVehicleStatus` + `GetLastVehiclePosition` toutes les 30 s |
| **Keyfob sync** | `CarCommand 21` envoyé toutes les 5 min pour détecter les changements locaux |
| **Réveil** | `CarCommand 9` envoyé automatiquement avant toute commande si `IsOffline = true` |

---

## Dépannage

**L'intégration ne se connecte pas**  
→ Vérifiez votre courriel et mot de passe dans l'application MyCar2 officielle.

**Les entités ne se mettent pas à jour**  
→ Le device est peut-être hors ligne (`binary_sensor.{nom}_hors_ligne = on`). Appuyez sur **Synchroniser** pour le réveiller.

**La position GPS est incorrecte ou absente**  
→ Normal si le véhicule est dans un parking souterrain. La position reprend dès que le signal GPS est disponible.

**Erreur après une mise à jour de HA**  
→ Supprimez l'intégration, redémarrez HA, et reconfigurez-la.

---

## Versions minimales

| Logiciel | Version |
|---|---|
| Home Assistant | 2024.1.0 |
| HACS | 1.34.0 |

---

## Licence

MIT
