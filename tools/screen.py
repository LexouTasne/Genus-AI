import os
import subprocess
import tempfile
import time

class ScreenTools:
    @staticmethod
    def screenshot():
        """Tira um print da tela e salva em um arquivo temporário."""
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        tmp.close()
        try:
            # Tenta scrot primeiro (comum em linux)
            subprocess.run(["scrot", tmp.name], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return tmp.name
        except:
            try:
                # Tenta gnome-screenshot
                subprocess.run(["gnome-screenshot", "-f", tmp.name], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return tmp.name
            except:
                return f"Erro: 'scrot' ou 'gnome-screenshot' não instalados."

    @staticmethod
    def read_screen():
        """Tenta ler o texto da tela usando OCR (pytesseract)."""
        path = ScreenTools.screenshot()
        if path.startswith("Erro"):
            return path
        
        try:
            import pytesseract
            from PIL import Image
            text = pytesseract.image_to_string(Image.open(path))
            os.unlink(path)
            return text if text.strip() else "Nenhum texto detectado na tela."
        except ImportError:
            return "Erro: 'pytesseract' ou 'Pillow' não instalados. Use pip install pytesseract Pillow."
        except Exception as e:
            return f"Erro ao processar OCR: {e}"
