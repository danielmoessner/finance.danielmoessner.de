def get_latest_picture(self):
    if self.latest_picture is not None:
        return self.latest_picture
    pictures = self.get_movie().pictures.order_by('date')
    if pictures.count() <= 0:
        return None
    self.latest_picture = pictures.last()
    self.save()
    return self.latest_picture
