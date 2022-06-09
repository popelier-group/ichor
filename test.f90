Program Hello
      implicit NONE
      Integer, Parameter :: sp = Selected_Real_Kind(6,37)    ! single
      Integer, Parameter :: dp = Selected_Real_Kind(15,307)  ! double
      Integer, Parameter :: qp = Selected_Real_Kind(33,4931) !

      Integer, Parameter :: wp = dp   
      real(kind=sp) :: x

      x = 2.0_wp

      Print *, x
      End Program Hello
